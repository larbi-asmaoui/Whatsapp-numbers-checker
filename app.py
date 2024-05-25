from yowsup.common.tools import Jid
from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers import YowLayerEvent
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers.coder import YowCoderLayer
from yowsup.stacks import YowStack
from yowsup.env import YowsupEnv
from yowsup.layers.protocol_contacts.protocolentities import *
import time
import os
from dotenv import load_dotenv

load_dotenv()

class WhatsappCheckLayer(YowInterfaceLayer):

    def __init__(self, phone_numbers):
        super(WhatsappCheckLayer, self).__init__()
        self.phone_numbers = phone_numbers
        self.checked_numbers = {}

    @ProtocolEntityCallback("success")
    def onSuccess(self, entity):
        print("Successfully connected.")
        self.check_numbers()

    @ProtocolEntityCallback("failure")
    def onFailure(self, entity):
        print("Failed to connect: %s" % entity.getReason())

    @ProtocolEntityCallback("presence")
    def onPresence(self, entity):
        if entity.getType() == "available":
            self.checked_numbers[entity.getFrom().split('@')[0]] = True
        else:
            self.checked_numbers[entity.getFrom().split('@')[0]] = False

    def check_numbers(self):
        contacts_entity = GetSyncIqProtocolEntity(self.phone_numbers)
        self.toLower(contacts_entity)

    @ProtocolEntityCallback("iq")
    def onIq(self, entity):
        if entity.getType() == 'result':
            print("Numbers checked:")
            valid_numbers = []
            for item in entity.getItems():
                number = item.getJid().split('@')[0]
                has_whatsapp = item.isValid()
                print(f"{number}: {'Has WhatsApp' if has_whatsapp else 'Does not have WhatsApp'}")
                if has_whatsapp:
                    valid_numbers.append(number)
            self.save_valid_numbers(valid_numbers)
            self.disconnect()

    def save_valid_numbers(self, valid_numbers):
        with open('valid.txt', 'w') as f:
            for number in valid_numbers:
                f.write(f"{number}\n")
        print(f"Valid numbers saved to valid.txt")

    def start(self):
        self.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))

    def disconnect(self):
        self.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_DISCONNECT))
        time.sleep(1) 

if __name__ == "__main__":
    phone_number = os.getenv("PHONE_NUMBER")
    whatsapp_password = os.getenv("WHATSAPP_PASSWORD")
    credentials = (phone_number, whatsapp_password)
    phone_numbers = []
    file_name = input("Enter the file name with .txt: ")
    while not file_name.endswith('.txt'):
        file_name = input("File not found. Enter the correct file name: ")
        try:
            with open(file_name, 'r') as f:
                phone_numbers = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            print("File not found. Please provide the correct file name.")
            exit(1)


    with open(file_name, 'r') as f:
        phone_numbers = [line.strip() for line in f.readlines()]
    
    
    stack = YowStack(
        (WhatsappCheckLayer(phone_numbers), )
    )
    print("Connecting to WhatsApp...")
    print(credentials)
    # stack.setCredentials(credentials)
    # stack.broadcastEvent(YowLayerEvent(YowsupEnv.EVENT_STATE_CONNECT))
    
    try:
        stack.loop(timeout=0.5, discrete=0.5)
    except Exception as e:
        print("An error occurred:", e)

