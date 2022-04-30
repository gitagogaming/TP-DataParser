import TouchPortalAPI
from TouchPortalAPI import TYPES
import requests
from threading import Thread
from time import sleep
import json
from functools import reduce
from pyquery import PyQuery

TPClient = TouchPortalAPI.Client("KillerBOSS.TPPlugin.DataParser", updateStatesOnBroadcast=False)
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

def HtmlParser(html, path):
    pq = PyQuery(html)
    tag = pq(path)
    print(tag.text())
    return tag.text()

def makeRequests(Method, endpoint, body, interval, result, listener):
    listenerData = listener[list(listener.keys())[0]]
    if result:
        TPClient.createState("KillerBOSS.TouchPortal.Plugin.DataParser.userState."+result, result, "")
    if listener and listenerData:
        while listenerData['status'] != "stop":
            if Method == "GET":
                requestResult = requests.get(url=listenerData["host"]+endpoint,
                     headers=json.loads(listenerData["header"]) if listenerData["header"] else None,
                      data=body)
                TPClient.stateUpdate("KillerBOSS.TouchPortal.Plugin.DataParser.userState."+result, requestResult.text)
            elif Method == "POST":
                requestResult = requests.post(url=listenerData["host"]+endpoint,
                     headers=json.loads(listenerData["header"]) if listenerData["header"] else None,
                      data=body)
                TPClient.stateUpdate("KillerBOSS.TouchPortal.Plugin.DataParser.userState."+result, requestResult.text)
            elif Method == "PUT":
                requestResult = requests.put(url=listenerData["host"]+endpoint,
                     headers=json.loads(listenerData["header"]) if listenerData["header"] else None,
                      data=body)
                TPClient.stateUpdate("KillerBOSS.TouchPortal.Plugin.DataParser.userState."+result, requestResult.text)
            elif Method == "DELETE":
                requestResult = requests.delete(url=listenerData["host"]+endpoint,
                     headers=json.loads(listenerData["header"]) if listenerData["header"] else None,
                      data=body)
                TPClient.stateUpdate("KillerBOSS.TouchPortal.Plugin.DataParser.userState."+result, requestResult.text)
            sleep(int(interval))
        if listenerData['status'] == "stop":
            pass # maybe remove all states thats created by the listener


def stateUpdate():
    while running:
        if requestListener and "KillerBOSS.TouchPortal.Plugin.DataParser.SetuprequestUsingListener.listoflistener" not in TPClient.choiceUpdateList:
            print(requestListener)
            if (listofListener := [list(x.keys())[0] for x in requestListener]) != TPClient.choiceUpdateList:
                TPClient.choiceUpdate("KillerBOSS.TouchPortal.Plugin.DataParser.SetuprequestUsingListener.listoflistener", listofListener)
        sleep(0.2)

@TPClient.on(TYPES.onConnect)
def onStart(data):
    print(data)
    Thread(target=stateUpdate).start()

@TPClient.on(TYPES.onAction)
def actionManager(data):
    global requestListener
    print(data)
    if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.DataParser.createHTTPlistener":
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
    if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.DataParser.SetuprequestUsingListener":
        if data['data'][0]['value'] != "" and (listener := findListener(data['data'][0]['value'])):
            listener[data['data'][0]['value']]['thread'] = Thread(target=makeRequests, args=(data['data'][1]['value'], data['data'][2]['value'],
            data['data'][3]['value'], data['data'][4]['value'], data['data'][5]['value'], listener))

            listener[data['data'][0]['value']]['thread'].start()
    if data['actionId'] == "KillerBOSS.TouchPortal.Plugin.DataParser.parsingData":
        if data['data'][3]['value'] == "Json":
            parsedData = jsonPathfinder(data['data'][1]['value'], data['data'][0]['value'])
        elif data['data'][3]['value'] == "Html":
            parsedData = HtmlParser(data['data'][1]['value'], data['data'][0]['value'])
        TPClient.createState("KillerBOSS.TouchPortal.Plugin.DataParser.userState."+data['data'][2]['value'], data['data'][2]['value'], str(parsedData))



TPClient.connect()

