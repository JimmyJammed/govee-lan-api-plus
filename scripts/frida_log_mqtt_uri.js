// scripts/frida_log_mqtt_uri.js

// ==============================================================================
// Govee LAN API Plus – Frida MQTT Hook
// ------------------------------------
//
// Description:
// Hooks the Govee Android app's MQTT publish methods to intercept outgoing MQTT
// messages and log them to Python via Frida's `send()` mechanism.
//
// Target Classes:
// - org.eclipse.paho.client.mqttv3.MqttAsyncClient
// - org.eclipse.paho.client.mqttv3.MqttMessage
//
// This script enables inspection of scene control payloads by capturing MQTT
// commands from Java overloads such as:
// - publish(topic, MqttMessage)
// - publish(topic, byte[], qos, retained)
// - publish(topic, MqttMessage, userContext, callback)
//
// Author: Jimmy Hickman
// License: MIT
// ==============================================================================

Java.perform(function () {
    try {
        var MqttAsyncClient = Java.use("org.eclipse.paho.client.mqttv3.MqttAsyncClient");
        var MqttMessage = Java.use("org.eclipse.paho.client.mqttv3.MqttMessage");
        var Arrays = Java.use("java.util.Arrays");

        console.log("📡 Attempting to hook MQTT publish methods...");

        // Hook connection (used for debugging MQTT broker connections)
        MqttAsyncClient.connect.overload().implementation = function () {
            console.log("🔌 Connecting to MQTT Broker...");
            return this.connect();
        };

        // Hook: publish(String topic, MqttMessage message)
        MqttAsyncClient.publish
            .overload('java.lang.String', 'org.eclipse.paho.client.mqttv3.MqttMessage')
            .implementation = function (topic, message) {
                sendToPythonLog(
                    "[MQTT] Publishing (MqttMessage) to topic: " + topic + "\n" +
                    "Message: " + message.toString()
                );
                return this.publish(topic, message);
            };

        // Hook: publish(String topic, byte[] payload, int qos, boolean retained)
        MqttAsyncClient.publish
            .overload('java.lang.String', '[B', 'int', 'boolean')
            .implementation = function (topic, payload, qos, retained) {
                var payloadString = Arrays.toString(payload);
                sendToPythonLog(
                    "[MQTT] Publishing (bytes) to topic: " + topic + "\n" +
                    "Payload: " + payloadString
                );
                return this.publish(topic, payload, qos, retained);
            };

        // Hook: publish(String topic, MqttMessage message, Object userContext, IMqttActionListener callback)
        MqttAsyncClient.publish
            .overload(
                'java.lang.String',
                'org.eclipse.paho.client.mqttv3.MqttMessage',
                'java.lang.Object',
                'org.eclipse.paho.client.mqttv3.IMqttActionListener'
            )
            .implementation = function (topic, message, userContext, callback) {
                sendToPythonLog(
                    "[MQTT] Publishing (MqttMessage with callback) to topic: " + topic + "\n" +
                    "Message: " + message.toString()
                );
                return this.publish(topic, message, userContext, callback);
            };

        /**
         * Sends the captured MQTT log data to the attached Python Frida session.
         *
         * @param {string} data - The message to log.
         */
        function sendToPythonLog(data) {
            try {
                send(data);
            } catch (e) {
                console.error("❌ Error sending data to Python log: " + e);
            }
        }

        console.log("✅ Successfully hooked MQTT publish methods and connection!");

    } catch (e) {
        console.error("❌ Error hooking classes: " + e);
    }
});