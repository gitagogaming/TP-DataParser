import TouchPortalAPI
from TouchPortalAPI import TYPES
import requests
from threading import Thread
from time import sleep
import json
from functools import reduce
from pyquery import PyQuery
import re
import sys

TPClient = TouchPortalAPI.Client("KillerBOSS.TPPlugin.DataParser", updateStatesOnBroadcast=False)


requestListener = []

def findListener(listenerName):
    for listener in requestListener:
        if listenerName == list(listener.keys())[0]:
            return listener
    return None

def jsonPathfinder(path, data):
    ## Load the Data into a json object
    data = json.loads(data)
    # Find Everything inside of brackets
    pathlist= re.findall(r"\[\'(.*?)\'\]", path)
    # Return the value of the path ONLY if it exists
    return reduce(lambda d, k: d.get(k, None) if isinstance(d, dict) else None, pathlist, data)

def HtmlParser(html, path):
    pq = PyQuery(html)
    tag = pq(path)
   # print(tag.text())
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
    while TPClient.isConnected():
        if requestListener and "KillerBOSS.TouchPortal.Plugin.DataParser.SetuprequestUsingListener.listoflistener" not in TPClient.choiceUpdateList:
            if (listofListener := [list(x.keys())[0] for x in requestListener]) != TPClient.choiceUpdateList:
                TPClient.choiceUpdate("KillerBOSS.TouchPortal.Plugin.DataParser.SetuprequestUsingListener.listoflistener", listofListener)
        sleep(0.2)

@TPClient.on(TYPES.onConnect)
def onStart(data):
    print(data)
    Thread(target=stateUpdate).start()
    
@TPClient.on('closePlugin')
def onShutdown(data):
    print("Plugin has been shutdown")

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
            print("parsedData", parsedData)
            
        elif data['data'][3]['value'] == "Html":
            parsedData = HtmlParser(data['data'][1]['value'], data['data'][0]['value'])
        TPClient.createState("KillerBOSS.TouchPortal.Plugin.DataParser.userState."+data['data'][2]['value'], data['data'][2]['value'], str(parsedData))




def main():
    global TPClient
    ret = 0
    try:
        TPClient.connect()
        print('TP Client closed.')
    except ConnectionResetError:
        print(f"Connection Reset Error:\n")
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting.")
    except Exception as err:
        from traceback import format_exc
        print(f"Exception in TP Client:\n{format_exc()}")
        ret = -1
    finally:
        print("The other shutdown")
        TPClient.disconnect()
        
        
    del TPClient
    return ret



if __name__ == "__main__":
    sys.exit(main())




