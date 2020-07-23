# This is an example scriptlet to pull AWS accounts
# Pulls a list of connector from /cloudview-api/rest/v1/aws/connectors
# Iterates the list of connectors per control per resource evaluations
# This example can be used for Azure or GCP by changing out the Cloud Provider and field map for account/subscription/project


import json
import os

username = "QUALYS_API_USERNAME"
password = "QUALYS_API_PASSWORD"
# use the below variable assignement if you are using os environment variables for storing the Qualys API User name and Password values
username = os.environ["QUALYS_API_USERNAME"]
password = os.environ["QUALYS_API_PASSWORD"]
BASEURL = os.environ["QUALYS_API_URL"]
#BASEURL = "QUALYS_API_URL"
pageNum = 0
notCompleteList = True

while notCompleteList:
    accountList = 'curl -k -s -u {}:{} -H "X-Requested-With:Curl" -H "Accept: application/json" -X "GET"  "{}/cloudview-api/rest/v1/aws/connectors?pageNo={}&pageSize=50"'.format(username,password,BASEURL,str(pageNum))
    accountQuery = os.popen(accountList).read()
    #print accountQuery
    response = json.loads(accountQuery)
    accountListContent = response['content']

    for account in accountListContent:
        kurl = 'curl -k -s -u {}:{} -H "X-Requested-With:Curl" -H "Accept: application/json" -X "GET"  "{}/cloudview-api/rest/v1/aws/evaluations/{}"'.format(username, password,BASEURL,str(account["awsAccountId"]))
        eval = os.popen(kurl).read()
        evalcontent = json.loads(eval)['content']
        try:
            for i in  range (len(evalcontent)):
                cid = int(evalcontent[i]["controlId"])
                criticality = str(evalcontent[i]["criticality"])
                remediationURL = str(BASEURL) + "/cloudview/controls/cid-" + str(evalcontent[i]["controlId"]) + ".html"
                notCompleteListResources = True
                resourcePage = 0
                while notCompleteListResources:
                    qurl = 'curl -k -s -u {}:{} -H "X-Requested-With:Curl" -H "Accept: application/json" -X "GET"  "{}/cloudview-api/rest/v1/aws/evaluations/{}/resources/{}?pageNo={}&pageSize=100"'.format(username, password,BASEURL,str(account["awsAccountId"]),cid, str(resourcePage))
                    result = os.popen(qurl).read()
                    #print (result)
                    resourceevaluation = json.loads(result)
                    count = len(resourceevaluation['content'])
                    for j in range(count):
                        resourcecontent = resourceevaluation['content'][j]
                        resourcecontent["controlName"] = evalcontent[i]["controlName"]
                        resourcecontent["controlId"] = evalcontent[i]["controlId"]
                        resourcecontent["remediationURL"] = remediationURL
                        resourcecontent["name"] = account["name"]
                        resourcecontent["criticality"] = criticality
                        print ((json.dumps(resourcecontent)))
                    if resourceevaluation['last']:
                        notCompleteListResources = False
                    else:
                        resourcePage+=1


        except:
            print("Error encountered")
            pass

    if response['last']:
        notCompleteList = False
    else:
        pageNum+=1
