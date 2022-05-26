class PubSubException(Exception): pass
class PubSub:
    """Interface to publish/subscribe
    """

    def __init__(self, jsonconfig, callback_function = None):
        self.mqtt, self.thingspeak = None, None

        self.mqtt_pub_topic = jsonconfig.get_str('mqtt_pub_topic')
        self.mqtt_sub_topic = jsonconfig.get_str('mqtt_sub_topic')
        thingspeak_apikey = jsonconfig.get_str('thingspeak_apikey')

        if self.mqtt_pub_topic or self.mqtt_sub_topic:
            import mqtt
            print("Setup MQTT connection")
            self.mqtt = mqtt.mqtt_create_client(jsonconfig)
            self.mqtt.connect()

        if self.mqtt_pub_topic:
            print("Setup MQTT pub topic:", self.mqtt_pub_topic)

        if self.mqtt_sub_topic and callback_function:
            print("Setup MQTT sub topic:", self.mqtt_sub_topic)
            self.mqtt.set_callback(callback_function)
            self.mqtt.subscribe(self.mqtt_sub_topic)

        if thingspeak_apikey:
            print("Setup ThingSpeak")
            from thingspeak import ThingSpeak
            self.thingspeak = ThingSpeak(apikey)

    def refresh_connection(self, timeout = None):
        import time
        reconnect = 0

        while self.mqtt.is_conn_issue():
            if timeout and reconnect > timeout:
                raise PubSubException("check_msg timeout")
            reconnect += 1
            self.mqtt.reconnect()
            time.sleep(1)

        if reconnect > 0:
            self.mqtt.resubscribe()

        return reconnect

    def check_msg(self):
        if self.mqtt_sub_topic:
            self.refresh_connection()
            return self.mqtt.check_msg()

    def publish(self, value):
        error_count = 0

        if self.mqtt:
            try:
                print("Publish to MQTT")
                self.refresh_connection()
                self.mqtt.publish(self.mqtt_pub_topic, str(value))
            except:
                print("MQTT publish error")
                error_count += 1

        if self.thingspeak:
            print("Publish to ThingSpeak")
            if self.thingspeak.post(field1 = value) != 200:
                print("ThingSpeak publish error")
                error_count += 1

        if error_count > 0:
            print("Publish error")
            raise "Publish error"
