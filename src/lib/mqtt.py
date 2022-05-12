# MQTT example
# https://github.com/micropython/micropython-lib/blob/master/micropython/umqtt.simple/example_sub.py
# https://github.com/micropython/micropython-lib/blob/master/micropython/umqtt.simple/example_pub_button.py

# from umqtt.robust import MQTTClient
from umqtt.robust2 import MQTTClient

def mqtt_create_client(config):
    client_name = config.get('mqtt_client_name') # 'esp32client'
    broker_name = config.get('mqtt_broker_name') # 'mqtt.beebotte.com'
    user        = config.get('mqtt_user') # 'token_XXXXXXXXXXXXXXXX'
    password    = config.get('mqtt_password') # 'token_XXXXXXXXXXXXXXXX'
    pub_topic   = config.get('mqtt_pub_topic') # 'doorplate/lux'

    # mqtt = MQTTClient(client_name, broker_name, user = user, password = password, port = 8883, ssl = True)
    mqtt = MQTTClient(client_name, broker_name, user = user, password = password, keepalive=60)
    # Print diagnostic messages when retries/reconnects happens
    mqtt.DEBUG = True
    # Information whether we store unsent messages with the flag QoS==0 in the queue.
    mqtt.KEEP_QOS0 = False
    # Option, limits the possibility of only one unique message being queued.
    mqtt.NO_QUEUE_DUPS = True
    # Limit the number of unsent messages in the queue.
    mqtt.MSG_QUEUE_MAX = 2
    # When you reconnect, all existing subscriptions are renewed.
    mqtt.RESUBSCRIBE = True
    return mqtt

if __name__ == '__main__':
    from jsonconfig import JsonConfig
    import time

    config = JsonConfig()
    topic = config.get('mqtt_pub_topic')
    mqtt = mqtt_create_client(config)
    mqtt.connect()
    while True:
        mqtt.publish(topic, 'Hello')
        time.sleep(10)
