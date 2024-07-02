from flask import Flask, send_from_directory
import os

app = Flask(__name__)

# Путь к директории, где находятся файлы
FILE_DIRECTORY = '/root/CODE/Avito/AvitoGoogle'

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(FILE_DIRECTORY, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

