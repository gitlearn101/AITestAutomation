import asyncio
import os
from subprocess import check_output

from boto3.resources.model import Action
from browser_use.agent.service import Agent
from browser_use.agent.views import ActionResult
from browser_use.browser.context import BrowserContext
from browser_use.controller.service import Controller
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr,BaseModel

# validation points
class CheckoutResult(BaseModel):
    login_status : str
    cart_status : str
    checkout_status : str
    total_update_status : str
    delivery_status : str
    confirmation_message : str

# customise agent behavior as a fallback mechanism by using Playwright
controller = Controller(output_model= CheckoutResult)

#this controller is unreliable. We will use AgentAI task but it is time consuming with Gemini model
@controller.action('Open website')
async def open_website(browser : BrowserContext):
    page = await browser.get_current_page()
    await page.goto('https://rahulshettyacademy.com/loginpagePractise/')
    #return ActionResult(extracted_content='browser opened')



@controller.action('Get Attribute and url of the page')
async def get_attr_url(browser : BrowserContext):
    page = await browser.get_current_page()
    current_url = page.url
    attr = await page.get_by_text("Shop Name").get_attribute('class')
    print(current_url)
    return ActionResult(extracted_content= f'current url is {current_url} and attr is {attr}' )

async def SiteValidation():
    os.environ["GEMINI_API_KEY"] = "<insert api key>"
    task = (
         'Important : I am UI Automation tester validating the tasks'
         'Open website'# https://rahulshettyacademy.com/loginpagePractise/'
         'Login with username and password. login Details available in the same page'
         'Get Attribute and url of the page'
         'After login, select first 2 products and add them to cart'
         'Then checkout and store the total value you see in the screen'
         'Increase the quantity of any product and check if total value update accordingly'
         'checkout and select country, agree terms and purchase'
         'verify thankyou message is displayed'

    )

    api_key = os.environ["GEMINI_API_KEY"]

    llm = ChatGoogleGenerativeAI(model= 'gemini-2.0-flash-exp',api_key= SecretStr(api_key))

    agent = Agent(task=task,llm= llm,controller=controller ,use_vision=True)

    history = await agent.run()
    history.save_to_file('agentresults.json')
    test_result = history.final_result()
    validated_result = CheckoutResult.model_validate_json(test_result)



    print(test_result)

    assert validated_result.confirmation_message == "Thank you! Your order will be delivered in next few weeks :-)."

asyncio.run(SiteValidation())
