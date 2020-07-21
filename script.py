# This is an example scriptlet to pull AWS accounts
# Pulls a list of connector from /cloudview-api/rest/v1/aws/connectors
# Iterates the list of connectors per control per resource evaluations
# This example can be used for Azure or GCP by changing out the Cloud Provider and field map for account/subscription/project


import json
import os

username = "REPLACE_ME_QUALYS_USERNAME"
password = "REPLACE_ME_QUALYS_PASSWORD"
BASEURL = "REPLACE_ME_BASE_URL"
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
                remediationURL = str(BASEURL) + "/cloudview/controls/cid-" + str(evalcontent[i]["controlId"]) + ".html"
                qurl = 'curl -k -s -u {}:{} -H "X-Requested-With:Curl" -H "Accept: application/json" -X "GET"  "{}/cloudview-api/rest/v1/aws/evaluations/{}/resources/{}"'.format(username, password,BASEURL,str(account["awsAccountId"]),cid)
                result = os.popen(qurl).read()
                resourceevaluation = json.loads(result)
                count = len(resourceevaluation['content'])
                for j in range(count):
                        resourcecontent = resourceevaluation['content'][j]
                        resourcecontent["controlName"] = evalcontent[i]["controlName"]
                        resourcecontent["controlId"] = evalcontent[i]["controlId"]
                        resourcecontent["remediationURL"] = remediationURL
                        print ((json.dumps(resourcecontent)))
        except:
            pass
    if response['last']:
        notCompleteList = False
    else:
        pageNum+=1
