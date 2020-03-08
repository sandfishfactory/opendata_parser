import urllib.request
from urllib.parse import urlparse, urlsplit
import json
import os
import importlib
import logging
import logging.config
import inspect

logger = logging.getLogger()


class OpendataParser():

    __download_dirname = "downloads"

    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        settings_path = os.path.join(self.current_dir, 'settings.json')
        with open(settings_path) as f:
            settings = json.load(f)
        self.api_urls = settings.get("appconfig").get("api_urls")
        self.file_storage = settings.get(
            "appconfig").get("file_storage").upper()
        self.download_path = os.path.join(
            self.current_dir, OpendataParser.__download_dirname
        )
        logging_config = settings.get("logging")
        logging.config.dictConfig(logging_config)

    def __download(self, download_list):
        allow_format_types = ("CSV", "XLSX", "XLS")
        resource_list = []

        for data in download_list:
            resources = data.get("resources", [])
            name = data.get("name", "")
            notes = data.get("notes", "")
            download_data = dict()

            #　ファイル保存先を作成する。
            if self.file_storage == "LOCAL":
                if not os.path.exists(self.download_path):
                    os.mkdir(self.download_path)

            for resource in resources:
                format_type = resource.get("format", "no_format").upper()
                if format_type in allow_format_types:
                    download_data["id"] = resource.get("package_id", "")
                    download_data["url"] = resource.get("url", "")
                    if download_data["url"]:
                        url_item = urlsplit(download_data["url"])
                        # urlsplitの2番目の要素はpath
                        path_item = url_item[2]
                        # /で文字列を分割して、一番最後の値がファイル名になっている
                        file_name = path_item.split("/")[-1]
                        file_path = os.path.join(self.download_path, file_name)
                        file_path = os.path.abspath(file_path)

                        if os.path.exists(file_path):
                            os.remove(file_path)

                        urllib.request.urlretrieve(
                            download_data["url"], file_path
                        )
                        download_data["file_path"] = file_path

                download_data["format"] = format_type
                download_data["name"] = name
                download_data["notes"] = notes
                logger.debug(download_data)
                resource_list.append(download_data)
        return resource_list

    def __parse(self):
        usrsrc = 'parser'
        parser_dir = os.listdir(os.path.join(self.current_dir, usrsrc))
        skip_class_name = ['__init__.py', 'base_parser.py']

        for u_src in parser_dir:
            if u_src.endswith('py') and u_src not in skip_class_name:
                path = usrsrc + '/' + u_src
                classpath = os.path.splitext(path)[0].replace(os.path.sep, '.')
                parser = importlib.import_module(classpath)
                clazz_list = inspect.getmembers(parser, inspect.isclass)

                for clazz in clazz_list:
                    if clazz[0] != 'BaseParser':
                        instance = clazz[1]()
                        instance.parse()

    def main(self):

        for url in self.api_urls:
            p = urlparse(url)
            query = urllib.parse.quote_plus(p.query, safe='=&')
            url = '{}://{}{}{}{}{}{}{}{}'.format(
                p.scheme, p.netloc, p.path,
                ';' if p.params else '', p.params,
                '?' if p.query else '', query,
                '#' if p.fragment else '', p.fragment)
            body = None
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as res:
                body = json.load(res)

            download_list = body["result"].get("results")
            logger.debug("URLの読み込み処理を開始")
            logger.debug("url:{}".format(url))
            logger.debug("##  ファイルダウンロード処理を開始")
            self.__download(download_list)
            logger.debug("##  ダウンロードしたファイルの解析処理を開始")
            self.__parse()
            logger.debug("URLの読み込み処理を終了")


if __name__ == '__main__':
    parser = OpendataParser()
    parser.main()
