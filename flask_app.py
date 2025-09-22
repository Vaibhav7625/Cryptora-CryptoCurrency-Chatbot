from flask import Flask, render_template, request, jsonify, redirect, url_for
from gemini_core import process_user_input
import os
import tempfile
import tempfile
import base64
import logging
import speech_recognition as sr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route("/splash")
def splash():
    return render_template("splash.html")

# Update the root route to redirect to splash page
@app.route("/")
def index():
    return redirect(url_for('splash'))

# Add a new route for the chat interface (previously your index route)
@app.route("/chat")
def chat():
    return render_template("index.html")

@app.route('/static/js/voice-input.js')
def serve_voice_input_js():
    return app.send_static_file('js/voice-input.js')

# Add this to check installed requirements
@app.route('/check-voice-requirements')
def check_voice_requirements():
    try:
        import speech_recognition
        from pydub import AudioSegment
        return jsonify({"status": "ok", "message": "Voice recognition dependencies are installed"})
    except ImportError as e:
        return jsonify({"status": "error", "message": f"Missing dependency: {str(e)}"})

# Add this improved error handler for the process-voice route
@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error, please try again"}), 500

@app.route("/process-voice", methods=["POST"])
def process_voice():
    if 'audio' not in request.files:
        logger.error("No audio file provided in request")
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    
    # Check if the file is empty
    if audio_file.filename == '':
        logger.error("Empty file submitted")
        return jsonify({"error": "Empty file submitted"}), 400
    
    # Get the content type from the request
    content_type = audio_file.content_type
    logger.info(f"Received audio file with content type: {content_type}")
    
    # Create a temporary file to store the audio with appropriate extension
    file_extension = '.webm'  # Default
    if 'mp4' in content_type:
        file_extension = '.mp4'
    elif 'ogg' in content_type:
        file_extension = '.ogg'
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_audio:
        temp_audio_path = temp_audio.name
        audio_file.save(temp_audio_path)
        logger.info(f"Saved audio file to temporary path: {temp_audio_path}")
    
    try:
        # Import modules here to handle potential import errors gracefully
        try:
            import speech_recognition as sr
            from pydub import AudioSegment
            
            # Convert audio to wav using pydub
            logger.info(f"Converting audio file from {file_extension} to wav: {temp_audio_path}")
            
            # Use different approach based on file type
            try:
                sound = AudioSegment.from_file(temp_audio_path)
                wav_path = temp_audio_path.replace(file_extension, '.wav')
                sound.export(wav_path, format="wav")
                logger.info(f"Successfully converted audio to WAV: {wav_path}")
            except Exception as conversion_error:
                logger.error(f"Error converting audio: {str(conversion_error)}")
                return jsonify({
                    "transcript": "",
                    "error": f"Error converting audio format: {str(conversion_error)}"
                }), 500
            
            # Use speech recognition to convert audio to text
            recognizer = sr.Recognizer()
            
            with sr.AudioFile(wav_path) as source:
                logger.info("Recording audio from file")
                audio_data = recognizer.record(source)
                logger.info("Recognizing speech...")
                
                try:
                    transcript = recognizer.recognize_google(audio_data)
                    logger.info(f"Transcript: {transcript}")
                except sr.UnknownValueError:
                    logger.warning("Speech recognition could not understand audio")
                    return jsonify({
                        "transcript": "",
                        "error": "Could not understand audio. Please speak clearly and try again."
                    }), 200
                except sr.RequestError as e:
                    logger.error(f"Could not request results from Google Speech Recognition service: {str(e)}")
                    return jsonify({
                        "transcript": "",
                        "error": "Speech recognition service unavailable. Please try again later."
                    }), 200
            
            # Clean up temporary files
            try:
                os.unlink(temp_audio_path)
                os.unlink(wav_path)
            except Exception as e:
                logger.warning(f"Could not delete temporary files: {str(e)}")
            
            return jsonify({"transcript": transcript})
            
        except ImportError as ie:
            logger.error(f"Import error: {str(ie)}. Using fallback method.")
            # Fallback to a simpler solution if speech recognition is not available
            return jsonify({
                "transcript": "I couldn't process your voice input. Please install the required packages: pip install SpeechRecognition pydub",
                "error": str(ie)
            }), 200
    
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        return jsonify({"transcript": "", "error": f"Error processing audio: {str(e)}"}), 500
    finally:
        # Ensure temp files are cleaned up even if an error occurs
        if os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except:
                pass
        wav_path = temp_audio_path.replace(file_extension, '.wav')
        if os.path.exists(wav_path):
            try:
                os.unlink(wav_path)
            except:
                pass

@app.route("/get-response", methods=["POST"])
def get_response():
    user_message = request.json.get("message", "")
    if not user_message:
        return jsonify({"response": "⚠️ No message received."})

    try:
        reply = process_user_input(user_message)

        # For WebView compatibility, using simpler HTML styling that renders well in mobile apps
        if isinstance(reply, dict):
            title = reply.get("title", "No Title")
            date = reply.get("date", "N/A")
            sentiment = reply.get("sentiment", "N/A")
            source = reply.get("source", "N/A")
            description = reply.get("description", "")
            link = reply.get("link", "#")

            if "Error fetching description" in description:
                description = "Error fetching the description."

            # Mobile-optimized HTML structure with inline styles for WebView compatibility
            formatted_reply = f"""
                <div style="background-color: rgba(20, 20, 30, 0.9); border-left: 4px solid #d4af37; 
                border-radius: 8px; padding: 12px; margin: 10px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.3);">
                    <p style="margin: 5px 0; color: #ffffff; font-size: 16px; font-weight: bold;">📰 {title}</p>
                    <p style="margin: 5px 0; color: #f1f1f1; font-size: 14px;">📅 <strong>Date:</strong> {date}</p>
                    <p style="margin: 5px 0; color: #f1f1f1; font-size: 14px;">😐 <strong>Sentiment:</strong> {sentiment}</p>
                    <p style="margin: 5px 0; color: #f1f1f1; font-size: 14px;">🌐 <strong>Source:</strong> {source}</p>
                    <p style="margin: 5px 0; color: #f1f1f1; font-size: 14px;">📝 <strong>Description:</strong> {description}</p>
                    <p style="margin: 5px 0; color: #d4af37; font-size: 14px;">🔗 <a href="{link}" target="_blank" style="color: #d4af37; text-decoration: underline;">{link}</a></p>
                </div>
            """
        else:
            # Apply inline styling for regular text responses as well
            formatted_text = reply.replace('\n', '<br>')
            formatted_reply = f"""
                <div style="background-color: rgba(20, 20, 30, 0.9); border-left: 4px solid #d4af37; 
                border-radius: 8px; padding: 12px; margin: 10px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.3);">
                    <p style="margin: 5px 0; color: #f1f1f1; font-size: 14px; line-height: 1.5;">{formatted_text}</p>
                </div>
            """

    except Exception as e:
        formatted_reply = f"""
            <div style="background-color: rgba(255, 50, 50, 0.2); border-left: 4px solid #ff3232; 
            border-radius: 8px; padding: 12px; margin: 10px 0;">
                <p style="margin: 5px 0; color: #ffffff; font-size: 14px;">❌ Error processing your request: {e}</p>
            </div>
        """

    return jsonify({"response": formatted_reply})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)