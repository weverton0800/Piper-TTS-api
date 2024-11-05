from flask import Flask, request, jsonify, send_file
import subprocess
import os
import threading
import time

app = Flask(__name__)

@app.route('/execute', methods=['POST'])
def execute_command():
    # Recebe os parâmetros do JSON
    data = request.get_json()
    text_param = data.get("text")
    output_file = data.get("output_file")

    if not text_param or not output_file:
        return jsonify({"error": "Parâmetros 'text' e 'output_file' são obrigatórios"}), 400

    # Valida o comprimento do texto
    if len(text_param) > 5000:
        return jsonify({"error": "O parâmetro 'text' excede o limite de 5000 caracteres"}), 400

    # Constrói o comando completo usando os parâmetros recebidos
    command = f"echo '{text_param}' | piper --model pt_BR-faber-medium --output_file {output_file}.wav && ffmpeg -i {output_file}.wav {output_file}.mp3"

    try:
        # Executa o comando
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return jsonify({
            "message": "Arquivo gerado com sucesso",
            "output_file": f"{output_file}.mp3"
        })
    except subprocess.CalledProcessError as e:
        # Retorna o erro se o comando falhar
        return jsonify({
            "output": e.stdout,
            "error": e.stderr
        }), 400

def delete_files_after_download(wav_file_path, mp3_file_path, delay=5):
    # Espera alguns segundos antes de remover os arquivos
    time.sleep(delay)
    try:
        if os.path.exists(wav_file_path):
            os.remove(wav_file_path)
        if os.path.exists(mp3_file_path):
            os.remove(mp3_file_path)
    except Exception as e:
        print(f"Erro ao remover arquivos: {e}")

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    # Caminho completo para os arquivos .wav e .mp3
    wav_file_path = f"{filename}.wav"
    mp3_file_path = f"{filename}.mp3"
    
    # Verifica se o arquivo .mp3 existe
    if not os.path.exists(mp3_file_path):
        return jsonify({"error": "Arquivo não encontrado"}), 404

    # Inicia uma thread para remover os arquivos após um atraso
    threading.Thread(target=delete_files_after_download, args=(wav_file_path, mp3_file_path)).start()

    # Envia o arquivo .mp3 para download
    return send_file(mp3_file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

