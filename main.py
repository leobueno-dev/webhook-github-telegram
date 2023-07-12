import httpx
import os
import logging
from fastapi import FastAPI, Request
__version__ = "0.0.1"


app = FastAPI()

TOKEN = os.getenv("TOKEN")  # Telegram Bot API Key
CHAT_ID = os.getenv("CHAT_ID")  # Telegram Chat ID


async def sendTgMessage(message: str):
    """
    Sends the Message to telegram with the Telegram BOT API
    """
    tg_msg = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        resp = await client.post(API_URL, json=tg_msg)
    print(resp.json())


@app.post("/hook")
async def recWebHook(req: Request):
    """
    Receive the Webhook and process the Webhook Payload to get relevant data
    Refer https://developer.github.com/webhooks/event-payloads for all GitHub Webhook Events and Payloads
    """
    body = await req.json()
    event = req.headers.get("X-Github-Event")
    message = ''
    if event == "star":  # check if the event is a star
        nos_stars = body["repository"]["stargazers_count"]
        starrer_username = body["sender"]["login"]
        repo_url = body["repository"]["html_url"]
        repo_name = body["repository"]["name"]
        message = f"{starrer_username} has starred the [{repo_name}]({repo_url}). \n\n The Total Stars are {nos_stars}"
    elif event == "issues":  # check if event is an issue
        issue_number = body["issue"]["number"]
        issue_action = body["action"]
        issue_title = body["issue"]["title"]
        issue_desc = body["issue"]["body"]
        issue_login = body["sender"]["login"]
        issue_repo = body["repository"]["full_name"]
        issue_repo_url = body["repository"]["html_url"]
        issue_url = body["issue"]["html_url"]
        isue_label = await getLabels(body["issue"]["labels"])

        if issue_action == "opened":
            logging.warning("Issue Opened")
            # message = f"*Issue* ([{issue_number}]({issue_url})) on [{issue_repo}]({issue_repo_url}) \n\nstatus: {issue_action} \nby: [{issue_login}]({issue_login}).\n\nTitle: *{issue_title}* \n\nDescription: {issue_desc} \n\nLabels: {isue_label}"

        if issue_action == "assigned":
            message = f"Issue ([{issue_number}]({issue_url})) on [{issue_repo}]({issue_repo_url}) *assigned* to: {issue_action} \n\nby: [{issue_login}]({issue_login}).\n\nTitle: *{issue_title}* \n\nLabels: {isue_label}"

        if issue_action == "closed":
            message = f"Issue ([{issue_number}]({issue_url})) on [{issue_repo}]({issue_repo_url}) *closed* by: [{issue_login}]({issue_login}).\n\nTitle: *{issue_title}* \n\n"

    elif event == "pull_request":  # check if event is a pull request
        # pprint.pprint(body)
        pr_number = body["number"]
        if body["pull_request"]["merged"] == True:
            pr_action = "merged"
        pr_action = body["action"]
        pr_title = body["pull_request"]["title"]
        pr_desc = body["pull_request"]["body"]
        pr_login = body["sender"]["login"]
        pr_login_url = body["sender"]["html_url"]
        pr_url = body["pull_request"]["html_url"]
        repo_name = body["repository"]["full_name"]
        repo_url = body["repository"]["html_url"]
        message = f"Pull Request([{pr_number}]({pr_url})) on [{repo_name}]({repo_url}) \nstatus: {pr_action} \nby: [{pr_login}]({pr_login_url}).\n\nTitle: *{pr_title}* \n"
        if (body["pull_request"]["requested_reviewers"]):
            message = f"{message}\nto: "
            for reviewers in body["pull_request"]["requested_reviewers"]:
                name = reviewers["login"]
                message = f"{message} *{name}*, "
            message = f"{message}. \n"
    if len(message) > 0:
        await sendTgMessage(message)


async def getLabels(labels):
    """
    Get the labels of the issue or pull request
    """
    label_list = []
    for label in labels:
        label_list.append(label["name"])
    return label_list
