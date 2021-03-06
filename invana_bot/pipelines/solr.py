from datetime import datetime
from invana_bot.settings import EXTRACTED_DATA_COLLECTION, DATABASE
from invana_bot.utils.url import get_urn
import pysolr


class SolrPipeline(object):
    def __init__(self, host=None,
                 port=None,
                 collection=None):
        self.core_name = collection
        self.solr_host = host
        self.solr = pysolr.Solr('http://{0}:{1}/solr/{2}'.format(self.solr_host, port, collection),
                                timeout=10)

    solr_date_fields = [
        'updated',
        'pub_date'
    ]

    solr_int_fields = [
    ]

    solr_content_fields = [

        'description',
        'content'
    ]

    def handle_date(self, v):
        new_v = None
        try:
            if type(v) == str:
                if "+" in v:
                    v = v.split("+")[0].strip()
                else:
                    v = v.replace("GMT", "").strip()
                new_v = datetime.strptime(v, '%a, %d %b %Y %H:%M:%S')
            else:
                new_v = v
        except Exception as e:
            pass
        return new_v

    def map_to_solr_datatypes(self, data):
        mapped_data = {}
        for k, v in data.items():
            if k in self.solr_date_fields:
                new_v = self.handle_date(v)
                if new_v:
                    mapped_data["{}_dt".format(k)] = new_v

            elif k in self.solr_int_fields:
                mapped_data["{}_i".format(k)] = v
            else:
                if k in self.solr_content_fields:
                    mapped_data["{}".format(k)] = v
                else:
                    mapped_data["{}_s".format(k)] = v

        if "html_s" in mapped_data:
            mapped_data['html'] = mapped_data['html_s']
            del mapped_data['html_s']
        return mapped_data

    @classmethod
    def from_crawler(cls, crawler):

        return cls(
            host=crawler.settings.get('PIPELINE_HOST', '127.0.0.1'),
            port=crawler.settings.get('HTTPCACHE_SOLR_PORT', '8983'),
            collection=crawler.settings.get('INVANA_BOT_EXTRACTED_DATA_COLLECTION', EXTRACTED_DATA_COLLECTION),
        )

    def clean_str(self, url):
        return url.replace(".", "-").replace(":", "-")

    def _flatten_headers(self, obj):
        flat_data = {}
        for k, v in obj.items():
            flat_data['headers_{}'.format(k)] = v
        return flat_data

    def process_item(self, item, spider):
        data = dict(item)
        data['updated'] = datetime.now()
        data = self.map_to_solr_datatypes(data=data)

        # print(data['pub_date_dt'], "================")
        if "pub_date_dt" in data.keys():
            del data['pub_date_dt']

        data['id'] = self.clean_str(get_urn(data['url_s']))
        self.solr.add([data])
        return item
