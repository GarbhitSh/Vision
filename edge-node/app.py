"""
VISION Edge Node - Flask Application
Captures frames from camera and forwards to Master Node
"""
from flask import Flask, jsonify, request
from camera.capture import CameraCapture
from camera.encoder import FrameEncoder
from config.settings import settings
from utils.logger import setup_logger
from utils.websocket_client import WebSocketClient
from utils.master_client import MasterClient
import threading
import time

app = Flask(__name__)
logger = setup_logger("edge_node")

# Global state
camera_capture = None
streaming_thread = None
streaming_active = False
frames_sent = 0
websocket_client = None
master_client = None


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    camera_status = "connected" if camera_capture and camera_capture.is_connected() else "disconnected"
    fps = camera_capture.get_fps() if camera_capture else 0.0
    
    return jsonify({
        "status": "healthy",
        "camera_status": camera_status,
        "fps": fps,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    })


@app.route("/camera/status", methods=["GET"])
def camera_status():
    """Get camera status"""
    if not camera_capture:
        return jsonify({
            "camera_id": settings.EDGE_NODE_ID,
            "is_connected": False,
            "error": "Camera not initialized",
            "source": settings.CAMERA_SOURCE
        }), 400
    
    info = camera_capture.get_camera_info()
    is_connected = camera_capture.is_connected()
    
    return jsonify({
        "camera_id": settings.EDGE_NODE_ID,
        "is_connected": is_connected,
        "source": str(camera_capture.source),
        "resolution": f"{info.get('width', 0)}x{info.get('height', 0)}",
        "fps": info.get("fps", 0),
        "format": info.get("format", "Unknown"),
        "error": None if is_connected else "Camera not connected"
    })


@app.route("/camera/test", methods=["GET"])
def test_camera():
    """Test camera capture - try to capture a frame"""
    if not camera_capture:
        return jsonify({
            "success": False,
            "error": "Camera not initialized"
        }), 400
    
    if not camera_capture.is_connected():
        return jsonify({
            "success": False,
            "error": "Camera not connected"
        }), 400
    
    try:
        frame = camera_capture.capture_frame()
        if frame is not None:
            return jsonify({
                "success": True,
                "frame_shape": list(frame.shape),
                "message": "Frame captured successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to capture frame"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/camera/reinitialize", methods=["POST"])
def reinitialize_camera():
    """Reinitialize camera"""
    global camera_capture
    
    try:
        # Release existing camera
        if camera_capture:
            camera_capture.release()
        
        # Reinitialize
        init_camera()
        
        if camera_capture and camera_capture.is_connected():
            return jsonify({
                "success": True,
                "message": "Camera reinitialized successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to reinitialize camera"
            }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def streaming_worker():
    """Worker thread for streaming frames"""
    global frames_sent, streaming_active, websocket_client, camera_capture
    
    encoder = FrameEncoder()
    # Reduce frame rate to match processing speed
    # If processing takes ~1.5s per frame, send at most 1 frame every 2 seconds
    # This prevents queue buildup and connection timeouts
    target_fps = 0.5  # 1 frame every 2 seconds (adjust based on processing speed)
    frame_interval = 1.0 / target_fps
    
    logger.info(f"Streaming worker started (target FPS: {target_fps})")
    
    while streaming_active:
        try:
            if not camera_capture or not camera_capture.is_connected():
                logger.warning("Camera not connected, stopping stream")
                streaming_active = False
                break
            
            if not websocket_client or not websocket_client.is_connected():
                # Try to reconnect
                logger.warning("WebSocket connection lost, reconnecting to master node...")
                if websocket_client:
                    try:
                        websocket_client.disconnect()
                    except:
                        pass
                websocket_client = WebSocketClient(
                    master_url=settings.MASTER_NODE_URL,
                    camera_id=settings.EDGE_NODE_ID
                )
                if not websocket_client.connect():
                    logger.warning("Failed to reconnect, retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                else:
                    logger.info("Successfully reconnected to master node")
            
            # Capture frame (read from camera but may skip sending if processing is slow)
            frame = camera_capture.capture_frame()
            if frame is None:
                time.sleep(frame_interval)
                continue
            
            # Encode frame
            frame_bytes = encoder.encode_jpeg(frame, quality=settings.FRAME_QUALITY)
            
            # Send frame
            if websocket_client.send_frame(
                frame_data=frame_bytes,
                width=camera_capture.width,
                height=camera_capture.height,
                fps=target_fps  # Use target FPS instead of camera FPS
            ):
                frames_sent += 1
                # Log every 10 frames to monitor progress
                if frames_sent % 10 == 0:
                    logger.info(f"Sent {frames_sent} frames (FPS: {target_fps})")
            else:
                logger.warning("Failed to send frame - connection may be lost")
                # Small delay before checking connection again
                time.sleep(0.1)
            
            # Throttle frame rate to match processing speed
            time.sleep(frame_interval)
            
        except Exception as e:
            logger.error(f"Error in streaming worker: {e}")
            time.sleep(1)
    
    logger.info("Streaming worker stopped")


def _start_streaming_internal(master_url=None, camera_id=None, fps=None, quality=None):
    """Internal function to start streaming (can be called without Flask request context)"""
    global streaming_active, streaming_thread, websocket_client
    
    master_url = master_url or settings.MASTER_NODE_URL
    camera_id = camera_id or settings.EDGE_NODE_ID
    fps = fps or settings.CAMERA_FPS
    quality = quality or settings.FRAME_QUALITY
    
    if streaming_active:
        logger.warning("Streaming already active")
        return False
    
    if not camera_capture or not camera_capture.is_connected():
        logger.error("Camera not connected")
        return False
    
    # Create WebSocket client (Socket.IO client uses HTTP URL)
    websocket_client = WebSocketClient(
        master_url=master_url,
        camera_id=camera_id
    )
    
    # Connect to master node
    if not websocket_client.connect():
        logger.error("Failed to connect to master node")
        return False
    
    # Start streaming thread
    streaming_active = True
    streaming_thread = threading.Thread(target=streaming_worker, daemon=True)
    streaming_thread.start()
    
    logger.info(f"Streaming started to {master_url} for camera {camera_id}")
    return True


@app.route("/stream/start", methods=["POST"])
def start_streaming():
    """Start streaming frames to master node (Flask route)"""
    data = request.get_json() or {}
    master_url = data.get("master_url", settings.MASTER_NODE_URL)
    camera_id = data.get("camera_id", settings.EDGE_NODE_ID)
    fps = data.get("fps", settings.CAMERA_FPS)
    quality = data.get("quality", settings.FRAME_QUALITY)
    
    success = _start_streaming_internal(master_url, camera_id, fps, quality)
    
    if not success:
        if streaming_active:
            return jsonify({"error": "Streaming already active"}), 400
        else:
            return jsonify({"error": "Failed to start streaming"}), 500
    
    return jsonify({
        "status": "started",
        "master_url": master_url,
        "camera_id": camera_id,
        "fps": fps
    })


@app.route("/stream/stop", methods=["POST"])
def stop_streaming():
    """Stop streaming frames"""
    global streaming_active, frames_sent, websocket_client
    
    if not streaming_active:
        return jsonify({"error": "Streaming not active"}), 400
    
    streaming_active = False
    
    # Wait for thread to finish
    if streaming_thread:
        streaming_thread.join(timeout=2)
    
    # Disconnect WebSocket
    if websocket_client:
        websocket_client.disconnect()
        websocket_client = None
    
    total_frames = frames_sent
    frames_sent = 0
    
    return jsonify({
        "status": "stopped",
        "frames_sent": total_frames
    })


def init_camera():
    """Initialize camera capture"""
    global camera_capture
    try:
        source = settings.CAMERA_SOURCE
        
        # Try to initialize camera
        camera_capture = CameraCapture(
            source=source,
            resolution=settings.CAMERA_RESOLUTION,
            fps=settings.CAMERA_FPS
        )
        
        success = camera_capture.initialize()
        
        if success:
            logger.info(f"Camera initialized successfully from source: {source}")
        else:
            logger.warning(f"Failed to initialize camera from source: {source}")
            
            # Try alternative sources if first attempt failed
            if isinstance(source, str) and source.isdigit():
                # Try other common camera indices
                for alt_source in [0, 1, 2]:
                    if str(alt_source) != source:
                        logger.info(f"Trying alternative camera source: {alt_source}")
                        camera_capture = CameraCapture(
                            source=str(alt_source),
                            resolution=settings.CAMERA_RESOLUTION,
                            fps=settings.CAMERA_FPS
                        )
                        if camera_capture.initialize():
                            logger.info(f"Camera initialized successfully from alternative source: {alt_source}")
                            break
                else:
                    logger.error("Failed to initialize camera from any source")
            else:
                logger.error(f"Camera source '{source}' is not valid")
    
    except Exception as e:
        logger.error(f"Failed to initialize camera: {e}")
        import traceback
        traceback.print_exc()


def register_with_master():
    """Register camera with master node"""
    global master_client
    
    if not camera_capture or not camera_capture.is_connected():
        logger.warning("Cannot register: Camera not connected")
        return False
    
    # Use MASTER_NODE_URL directly (should be http://localhost:8000)
    api_url = settings.MASTER_NODE_URL
    if api_url.startswith('ws://'):
        api_url = api_url.replace('ws://', 'http://')
    elif api_url.startswith('wss://'):
        api_url = api_url.replace('wss://', 'https://')
    
    # Remove any paths
    if '/' in api_url and '://' in api_url:
        # Keep protocol and host, remove path
        parts = api_url.split('/', 3)
        if len(parts) >= 3:
            api_url = f"{parts[0]}//{parts[2]}"
    
    master_client = MasterClient(api_url)
    
    # Check if master is available
    if not master_client.check_health():
        logger.warning("Master node not available, will retry later")
        return False
    
    # Get camera info
    info = camera_capture.get_camera_info()
    resolution = f"{info.get('width', 1920)}x{info.get('height', 1080)}"
    fps = info.get('fps', settings.CAMERA_FPS)
    
    # Register camera
    success = master_client.register_camera(
        camera_id=settings.EDGE_NODE_ID,
        edge_node_id=settings.EDGE_NODE_ID,
        location=f"Edge Node {settings.EDGE_NODE_ID}",
        resolution=resolution,
        fps=fps
    )
    
    if success:
        logger.info("Camera registered with master node")
        # Auto-start streaming
        time.sleep(1)  # Wait a bit
        _start_streaming_internal()
    
    return success


if __name__ == "__main__":
    logger.info("Starting VISION Edge Node...")
    logger.info(f"Edge Node ID: {settings.EDGE_NODE_ID}")
    logger.info(f"Master Node URL: {settings.MASTER_NODE_URL}")
    
    # Initialize camera
    init_camera()
    
    # Register with master node and start streaming
    if camera_capture and camera_capture.is_connected():
        # Try to register in a separate thread to not block startup
        def register_thread():
            time.sleep(2)  # Wait for master node to be ready
            register_with_master()
        
        threading.Thread(target=register_thread, daemon=True).start()
    
    # Run Flask app
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=settings.DEBUG,
        threaded=True
    )

