from http.server import BaseHTTPRequestHandler, HTTPServer
import json

translations = {
    'en': {'es': {}, 'fr': {}},
    'es': {'en': {}, 'fr': {}},
    'fr': {'en': {}, 'es': {}},
}

class TranslationHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/translations'):
            params = self.path.split('?')
            if len(params) == 2:
                query_string = params[1]
                query_params = dict(p.split('=') for p in query_string.split('&'))
                word = query_params.get('word')
                target_language = query_params.get('target_language')
                source_language = query_params.get('source_language', 'en')

                if word and target_language and source_language in translations:
                    translation = self.get_translation(word, source_language, target_language)
                    if translation:
                        self._set_headers(200)
                        self.wfile.write(json.dumps(translation).encode())
                        return
        self._set_headers(400)
        self.wfile.write(json.dumps({'error': 'Invalid request'}).encode())

    def do_POST(self):
        if self.path == '/translations':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                new_translation = json.loads(post_data.decode())
                if self.validate_translation(new_translation):
                    source_language = new_translation.get('source_language', 'en')
                    if source_language in translations:
                        self.add_translation(new_translation)
                        self._set_headers(201)
                        self.wfile.write(json.dumps({'message': 'Translation added'}).encode())
                        return
            except (ValueError, json.JSONDecodeError):
                pass
        self._set_headers(400)
        self.wfile.write(json.dumps({'error': 'Invalid request'}).encode())

    def do_PUT(self):
        if self.path.startswith('/translations'):
            params = self.path.split('/')
            if len(params) == 3:
                translation_id = int(params[2])
                content_length = int(self.headers['Content-Length'])
                put_data = self.rfile.read(content_length)
                try:
                    updated_translation = json.loads(put_data.decode())
                    if self.validate_translation(updated_translation):
                        source_language = updated_translation.get('source_language', 'en')
                        if source_language in translations:
                            if self.update_translation(translation_id, updated_translation):
                                self._set_headers(200)
                                self.wfile.write(json.dumps({'message': 'Translation updated'}).encode())
                                return
            except (ValueError, json.JSONDecodeError):
                pass
        self._set_headers(400)
        self.wfile.write(json.dumps({'error': 'Invalid request'}).encode())

    def do_DELETE(self):
        if self.path.startswith('/translations'):
            params = self.path.split('/')
            if len(params) == 3:
                translation_id = int(params[2])
                if self.delete_translation(translation_id):
                    self._set_headers(204)
                    return
        self._set_headers(400)
        self.wfile.write(json.dumps({'error': 'Invalid request'}).encode())

    def validate_translation(self, translation):
        required_fields = ['word', 'target_language', 'translation']
        source_language = translation.get('source_language', 'en')

        if not all(field in translation for field in required_fields):
            return False

        if source_language not in translations:
            return False

        if translation['target_language'] not in translations[source_language]:
            return False

        return True

    def get_translation(self, word, source_language, target_language):
        if word in translations[source_language][target_language]:
            return {
                'word': word,
                'source_language': source_language,
                'target_language': target_language,
                'translation': translations[source_language][target_language][word]
            }
        return None

    def add_translation(self, translation):
        source_language = translation.get('source_language', 'en')
        target_language = translation['target_language']
        word = translation['word']
        translations[source_language][target_language][word] = translation['translation']

    def update_translation(self, translation_id, updated_translation):
        source_language = updated_translation.get('source_language', 'en')
        target_language = updated_translation['target_language']
        word = updated_translation['word']
        if translations[source_language][target_language].get(word):
            translations[source_language][target_language][word] = updated_translation['translation']
            return True
        return False

    def delete_translation(self, translation_id):
        for source_language in translations:
            for target_language in translations[source_language]:
                for word in list(translations[source_language][target_language].keys()):
                    if translations[source_language][target_language][word] == translation_id:
                        del translations[source_language][target_language][word]
                        return True
        return False

def run_server():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, TranslationHandler)
    print('Starting server...')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
