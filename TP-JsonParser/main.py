import TouchPortalAPI
from TouchPortalAPI import TYPES
import requests
from threading import Thread
from time import sleep
import json
from functools import reduce

TPClient = TouchPortalAPI.Client("KillerBOSS.TPPlugin.JsonParser", updateStatesOnBroadcast=False)
running = True


requestListener = []

def findListener(listenerName):
    for listener in requestListener:
        if listenerName == list(listener.keys())[0]:
            return listener
    
    return None

def jsonPathfinder(path, data):
    pathlist = []
    print(data)
    data = json.loads(data)
    for path in path.split("."):
        try:
            pathlist.append(int(path))
        except ValueError:
            pathlist.append(path)
    print(pathlist)
    return reduce(lambda a, b: a[b], pathlist, data)

def makeRequests(Method, endpoint, body, interval, result, listener):
    listenerData = listener[list(listener.keys())[0]]
    TPClient.createState("KillerBOSS.TouchPortal.Plugin.JsonParser.userState."+result, result, "")
    if listener and listenerData:
        while listenerData['status'] != "stop":
            if Method == "GET":
                requestResult = requests.get(url=listenerData["host"]+endpoint, headers=json.loads(listenerData["header"]))
                TPClient.stateUpdate("KillerBOSS.TouchPortal.Plugin.JsonParser.userState."+result, requestResult.text)
            sleep(int(interval))
        if listenerData['status'] == "stop":
            pass # maybe remove all states thats created by the listener


def stateUpdate():
    while running:
        if requestListener and "KillerBOSS.TouchPortal.Plugin.JsonParser.SetuprequestUsingListener.listoflistener" not in TPClient.choiceUpdateList:
            print(requestListener)
            if (listofListener := [list(x.keys())[0] for x in requestListener]) != TPClient.choiceUpdateList:
                TPClient.choiceUpdate("KillerBOSS.TouchPortal.Plugin.JsonParser.SetuprequestUsingListener.listoflistener", listofListener)
        sleep(0.2)

@TPClient.on(TYPES.onConnect)
def onStart(data):
    print(data)
    Thread(target=stateUpdate).start()

@TPClient.on(TYPES.onAction)
def actionManager(data):
    global requestListener
    print(data)
    if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.JsonParser.createHTTPlistener":
        if data['data'][0]['value'] != "" and data['data'][1]['value'] != "":
            if not findListener(data['data'][0]['value']): # check if is already created
                requestListener.append(
                    {
                        data['data'][0]['value']: {
                            "host": data['data'][1]['value'],
                            "header": data['data'][2]['value'],
                            "thread":  Thread,
                            "status": "standby"
                        }
                    }
                )
    if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.JsonParser.SetuprequestUsingListener":
        if data['data'][0]['value'] != "" and (listener := findListener(data['data'][0]['value'])):
            listener[data['data'][0]['value']]['thread'] = Thread(target=makeRequests, args=(data['data'][1]['value'], data['data'][2]['value'],
            data['data'][3]['value'], data['data'][4]['value'], data['data'][5]['value'], listener))

            listener[data['data'][0]['value']]['thread'].start()
    if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.JsonParser.parsingData":
        parsedData = jsonPathfinder(data['data'][1]['value'], data['data'][0]['value'])
        print(parsedData)
        TPClient.createState("KillerBOSS.TouchPortal.Plugin.JsonParser.userState."+data['data'][2]['value'], data['data'][2]['value'], str(parsedData))



TPClient.connect()

