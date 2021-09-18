import urequests

class ThingSpeak:
    """
    Interface to ThingSpeak
    """


    def __init__(self, apikey):
        self._apikey = apikey


    def post(self, field1=None, field2=None, field3=None, field4=None, field5=None, field6=None, field7=None, field8=None):
        field_array = [field1, field2, field3, field4, field5, field6, field7, field8]
        return self.post_fields(field_array)


    def post_fields(self, field_array):
        url = 'https://api.thingspeak.com/update?api_key={}'.format(self._apikey)
        for i, v in enumerate(field_array):
            if v is not None:
                url += '&field{}={}'.format(i + 1, v)
        print("HTTP GET {}".format(url))
        resp = urequests.get(url)
        code = resp.status_code
        resp.close()
        return code
