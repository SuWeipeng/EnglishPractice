class AutoTranslator:
    def __init__(self,who='googletrans',src_lang='zh-cn', to_lang='en'):
        self.who  = who
        self.src  = src_lang
        self.dest = to_lang
        if self.who == 'googletrans':
            from googletrans import Translator
            self.translator = Translator()
        elif self.who == 'google_trans_new':
            from google_trans_new import google_translator
            self.translator = google_translator(url_suffix="com",timeout=30)
    def trans(self, text):
        res = None
        if self.who == 'googletrans':
            res = self.translator.translate(text, src=self.src, dest=self.dest).text
        elif self.who == 'google_trans_new':
            res = self.translator.translate(text,lang_src=self.src,lang_tgt=self.dest)
        return res