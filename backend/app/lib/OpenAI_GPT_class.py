from openai import OpenAI
import openai,time,os,threading as th,json
import lib.logger as logger
import datetime
os.makedirs('log', exist_ok=True)
logger = logger.setup_logger(f'log/{datetime.datetime.now().strftime("%Y-%m-%d_%H")}_backend.log')

class openai_GPT:
    def __init__(self,model="gpt-3.5-turbo-0125",gpt_key="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"):
        self.model_name=model
        self.api_key=gpt_key
        self.openai_client = OpenAI(
            api_key=self.api_key,)
        self.gpt_lock=th.Lock()
        self.APIValidation=False
        self.complete_tokens=0
        self.prompt_tokens=0
        self.error_message={
            401:"Invalid Authentication",
            403:"Country, region, or territory not supported",
            429:"Rate limit reached for requests",
            500:"The server had an error while processing your request",
            503:"The engine is currently overloaded, please try again later",
        }
        if not self.APIValidation:
            self.Check_apikey()


    def Check_apikey(self):
        try:
            response=self.openai_client.chat.completions.create(
                model=self.model_name,
                messages= [
                    {"role": "system", "content":f"You are a API Checker"},
                    {"role": "user", "content":f"give me a yes if API is working"},
                    ],
                temperature=0,
                max_tokens=5,
            )
            if dict(response).get('choices',None) is not None:
                self.APIValidation=True
                # logger.info(f"{th.current_thread().name} API key is valid")
        except openai.AuthenticationError as e:
            logger.error(f"{th.current_thread().name} code : {e.status_code}, {self.error_message[e.status_code]}")
            os._exit(0)

    def  ChatGPT_reply(self,systemPrompt='',userprompt='',input_text='',temperature=0.5,max_tokens=256,pb=None,lock=None,assistant_content=""):
        if input_text:
            for _ in range(1):
                self.gpt_lock.acquire()
                self.gpt_lock.release()
                time.sleep(0.1)
                try:
                    response=self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages= [
                        {"role": "system", "content":systemPrompt},
                        {"role": "user", "content":f"{userprompt}\n {input_text}"},
                        {"role": "assistant", "content": f"{assistant_content}"}
                        ],

                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={ "type": "json_object" }
                    )

                    if dict(response).get('choices',None) is not None:
                        self.APIValidation=True
                        self.complete_tokens+=response.usage.completion_tokens
                        self.prompt_tokens+=response.usage.prompt_tokens
                        claim_text=response.choices[0].message.content
                        return claim_text
                except:
                    self.gpt_lock.acquire()
                    time.sleep(2)
                    self.gpt_lock.release()
                    continue
        else:
            logger.debug("Text input empty, please check your input text")
            return 1

if __name__=="__main__":
    client=openai_GPT()
    systemPrompt="You Are A professor"
    userprompt="please rewrite the the context into a story and give the confidence score in json:"
    input_text="The quick brown fox jumps over the lazy dog"

    print(client.ChatGPT_reply(systemPrompt=systemPrompt,userprompt=userprompt,input_text=input_text,assistant_content=""))
    # with open('myfile.txt', 'r') as file1:
    #     input_text = file1.readlines()
    # # print(client.ChatGPT_reply(systemPrompt='',userprompt='',input_text='',assistant_content=""))
    # with open('myfile.txt', 'w') as file1:
    #     input_text = file1.readlines()
