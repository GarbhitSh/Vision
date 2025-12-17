"""
WebSocket client for sending frames to master node
"""
import socketio
import socketio.exceptions
import base64
import json
import time
from datetime import datetime
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger("websocket_client")


class WebSocketClient:
    """WebSocket client for frame streaming"""
    
    def __init__(self, master_url: str, camera_id: str):
        """
        Initialize WebSocket client
        
        Args:
            master_url: Master node WebSocket URL
            camera_id: Camera identifier
        """
        self.master_url = master_url
        self.camera_id = camera_id
        self.sio = None
        self.connected = False
        self.frame_id = 0
        self.reconnect_delay = 5
        self.max_reconnect_attempts = None  # Unlimited
        
    def connect(self):
        """Connect to master node"""
        try:
            # Create Socket.IO client
            # The client will automatically use websocket if available, polling otherwise
            self.sio = socketio.Client(
                reconnection=True,
                reconnection_delay=self.reconnect_delay
            )
            
            connection_event = {'connected': False, 'error': None}
            
            @self.sio.on('connect')
            def on_connect():
                self.connected = True
                connection_event['connected'] = True
                logger.info(f"Connected to master node: {self.master_url}")
            
            @self.sio.on('disconnect')
            def on_disconnect():
                self.connected = False
                logger.warning(f"Disconnected from master node (reason: connection lost)")
            
            @self.sio.on('connect_error')
            def on_error(data):
                connection_event['error'] = data
                logger.error(f"Connection error: {data}")
            
            # Connect to Socket.IO server
            # Socket.IO client expects http:// URL, not ws://
            connect_url = self.master_url
            if connect_url.startswith('ws://'):
                connect_url = connect_url.replace('ws://', 'http://')
            elif connect_url.startswith('wss://'):
                connect_url = connect_url.replace('wss://', 'https://')
            
            logger.info(f"Connecting to Socket.IO server: {connect_url}")
            
            # Connect with timeout
            try:
                # Connect (this is blocking, will raise exception if fails)
                # The client will automatically use websocket if available, polling otherwise
                self.sio.connect(connect_url, wait_timeout=10)
                
                # Wait a bit for connection to establish and event handlers to fire
                import time
                max_wait = 2.0  # Maximum wait time
                wait_interval = 0.1
                waited = 0.0
                
                while waited < max_wait:
                    if self.sio.connected and connection_event.get('connected', False):
                        self.connected = True
                        logger.info("Socket.IO connection confirmed")
                        return True
                    if connection_event.get('error'):
                        break
                    time.sleep(wait_interval)
                    waited += wait_interval
                
                # Check final connection state
                if self.sio.connected:
                    self.connected = True
                    return True
                else:
                    error_msg = connection_event.get('error', 'Connection timeout')
                    logger.error(f"Connection failed: {error_msg}")
                    if self.sio:
                        try:
                            self.sio.disconnect()
                        except:
                            pass
                    self.connected = False
                    return False
                    
            except socketio.exceptions.ConnectionError as e:
                logger.error(f"Socket.IO connection error: {e}")
                if self.sio:
                    try:
                        self.sio.disconnect()
                    except:
                        pass
                self.connected = False
                return False
            except Exception as e:
                logger.error(f"Unexpected connection error: {e}")
                import traceback
                traceback.print_exc()
                if self.sio:
                    try:
                        self.sio.disconnect()
                    except:
                        pass
                self.connected = False
                return False
            
        except Exception as e:
            logger.error(f"Failed to connect to master node: {e}")
            import traceback
            traceback.print_exc()
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from master node"""
        if self.sio and self.connected:
            try:
                self.sio.disconnect()
                self.connected = False
                logger.info("Disconnected from master node")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
    
    def send_frame(self, frame_data: bytes, width: int, height: int, fps: float = 30.0) -> bool:
        """
        Send frame to master node
        
        Args:
            frame_data: JPEG encoded frame bytes
            width: Frame width
            height: Frame height
            fps: Frames per second
        
        Returns:
            True if sent successfully, False otherwise
        """
        # Check connection state
        if not self.sio:
            return False
        
        # Check if actually connected (sio.connected is the source of truth)
        if not hasattr(self.sio, 'connected') or not self.sio.connected:
            self.connected = False
            return False
        
        try:
            # Limit frame size to prevent connection issues (max 1MB base64 = ~750KB raw)
            max_frame_size = 750 * 1024
            if len(frame_data) > max_frame_size:
                # Compress or skip if too large
                logger.warning(f"Frame too large ({len(frame_data)} bytes), skipping")
                return False
            
            # Encode frame to base64
            frame_b64 = base64.b64encode(frame_data).decode('utf-8')
            
            # Create message
            message = {
                "camera_id": self.camera_id,
                "frame_id": self.frame_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "frame_data": frame_b64,
                "width": width,
                "height": height,
                "fps": fps
            }
            
            # Send via Socket.IO (automatically serializes dict to JSON)
            # Use callback to check if message was sent successfully
            try:
                self.sio.emit('frame', message)
                self.frame_id += 1
                return True
            except socketio.exceptions.BadNamespaceError:
                logger.error("Bad namespace error - connection may be lost")
                self.connected = False
                return False
            except Exception as emit_error:
                logger.error(f"Error emitting frame: {emit_error}")
                # Check if connection is still valid
                if not self.sio.connected:
                    self.connected = False
                return False
            
        except Exception as e:
            logger.error(f"Error sending frame: {e}")
            import traceback
            traceback.print_exc()
            # Only mark as disconnected if connection is actually lost
            if self.sio and not self.sio.connected:
                self.connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if connected"""
        if not self.sio:
            return False
        # Check both our flag and the actual Socket.IO connection state
        return self.connected and hasattr(self.sio, 'connected') and self.sio.connected

