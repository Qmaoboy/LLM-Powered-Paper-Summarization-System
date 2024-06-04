import threading as th
from lib.mysql_class import mysql_db_client
from lib.OpenAI_GPT_class import openai_GPT
from lib.utilized import *
from lib.ppt_maker import make_ppt
from lib.BLIP_image_Description import Func_blip_
from lib.CLIP_Image_text_Similarty import Func_clip_
import json,time,glob
from queue import Queue
import lib.logger as logger
import datetime
os.makedirs('log', exist_ok=True)
logger = logger.setup_logger(f'log/{datetime.datetime.now().strftime("%Y-%m-%d_%H")}_backend.log')

BLIPprocessor=None
BLIPmodel=None
gc.collect()
torch.cuda.empty_cache()

class gpt_Worker(th.Thread):
    def __init__(self,pdf_path,job_all,q_in,q_out,q_in_spent,q_out_spent,in_lock,out_lock,terminal,args)-> None:
        th.Thread.__init__(self)
        self.args=args
        self.pdf_path=pdf_path
        self.job_all=job_all
        self.q_in = q_in
        self.q_out = q_out
        self.q_in_spent=q_in_spent
        self.q_out_spent=q_out_spent
        self.in_lock = in_lock
        self.out_lock = out_lock
        self.terminal=terminal
        self.GPTmodel=self.args['MainConfig']['GPTmodel']
        self.gpt_Dubug_mode=self.args['MainConfig']['gpt_Dubug_mode']
        self.clip_Dubug_mode=self.args['MainConfig']['clip_Dubug_mode']
        self.Paper_gpt=openai_GPT(self.GPTmodel)
        self.client=mysql_db_client(self.args)
        self.regen_times=1
        self.reply_dic={}
        self.task="paper"
        for i in self.args['sql_config']['table_name']:
            self.client.create_table(i)
        result = self.client.Show_tables()
        os.system(f"echo {result}")

    def check_struct(self,target_dic,col_name)->list:
        if isinstance(target_dic[col_name],str):
            val=target_dic[col_name].split(",")
        elif isinstance(target_dic[col_name],dict):
            val=target_dic[col_name].values()
        else:
            if isinstance(target_dic[col_name][0],dict):
                val_list=[]
                for i in target_dic[col_name]:
                    val_list+=i.values()
                val=val_list
            else:
                val=target_dic[col_name]
        return list(val)

    def Get_openai_GPT(self,pb,pdf_filename):
        content_dic={}
        if self.gpt_Dubug_mode:
            logger.info(f"{th.current_thread().name} perform {self.task} Summerization on {pb}")
        if self.task=="paper":
            text,toc,image_id=pdf_reader(self.pdf_path,pb,pdf_filename,self.client,self.gpt_Dubug_mode)
            text_split_for_gpt,prefix=decompose_text(text)
        elif self.task=="news":
            text=News_reader(self.pdf_path,pb,pdf_filename,self.client,self.gpt_Dubug_mode)
            text_split_for_gpt,prefix=decompose_text(text)

        for i in range(self.regen_times):
            try:
                author_assistant="Question:"+str(self.args['GPT_Prompt']['author_ques'])+"Answer:"+str(self.args['GPT_Prompt']['author_ans'])
                authreply = self.Paper_gpt.ChatGPT_reply(str(self.args['GPT_Prompt']['auth_sys_prompt']),str(self.args['GPT_Prompt']['author_prompt']),prefix,temperature=0,max_tokens=1024,pb=pb,assistant_content=author_assistant)
                titi_dic=json.loads(authreply)
                break
            except:
                logger.debug(f"{th.current_thread().name} {pb} json Load Fail {i} ")
                continue
        reply=''
        for i in range(len(text_split_for_gpt)):
            input_text=str(reply)+text_split_for_gpt[i]
            if i ==len(text_split_for_gpt)-1:
                for i in range(self.regen_times):

                    sum_assistant_prompt="Question:"+str(self.args['GPT_Prompt']['summaery_ques'])+"Answer:"+str(self.args['GPT_Prompt']['summaery_ans'])
                    try:
                        reply=self.Paper_gpt.ChatGPT_reply(str(self.args['GPT_Prompt']['content_sys_prompt']),str(self.args['GPT_Prompt']['content_prompt']),input_text,temperature=0,max_tokens=1024,pb=pb,assistant_content=sum_assistant_prompt)
                        content_dic=json.loads(reply)
                        break
                    except:
                        logger.debug(f"{th.current_thread().name} {pb} json Load Fail {i}")
                        continue
            else:
                reply=self.Paper_gpt.ChatGPT_reply(str(self.args['GPT_Prompt']['content_sys_prompt']),str(self.args['GPT_Prompt']['content_Split_prompt']),input_text,temperature=0,max_tokens=1024,pb=pb,assistant_content="")

        ################################
        title_name=titi_dic['title_name']
        author_name=self.check_struct(titi_dic,'author_name')
        organization_name=self.check_struct(titi_dic,'organization_name')
        keywords=content_dic["keywords"]+[author_name[0],organization_name[0]]
        keypoints=self.check_struct(content_dic,'keypoints')
        with open(os.path.join(self.pdf_path,f"{pdf_filename}.pdf"), 'rb') as file_:
            self.reply_dic={
                'Paper_name': pb,
                'title_name': title_name,
                'Project_name': self.pdf_path.split("\\")[-1],
                'keypoints': ",".join(keypoints),
                'author_name':",".join(author_name),
                'organization_name':",".join(organization_name),
                'keywords' :",".join(keywords),
                'Image_id': image_id,
                'Logit_per_image': {},
                'image_Description':{},
                'Represent_image':[],
                'prompt_tokens':self.Paper_gpt.prompt_tokens,
                'complete_tokens':self.Paper_gpt.complete_tokens,
                'Status':1,
                'pdf_file_byte': file_.read()
            }
        if self.gpt_Dubug_mode:
            print(self.reply_dic['title_name'])
            print(self.reply_dic['Project_name'])
            print(self.reply_dic['author_name'])
            print(self.reply_dic['organization_name'])
            print(self.reply_dic['Paper_name'])

        return self.reply_dic


    def run(self):
        if self.gpt_Dubug_mode:
            logger.info(f"{th.current_thread().name} Start GPT Generateion")
        while True:
            self.in_lock.acquire()
            if self.q_in.qsize()>0:
                pb = self.q_in.get()
                self.in_lock.release()
                pdf_filename=pb.split('\\')[-1].split(".")[0]
                pb=pdf_filename.strip()
                # text,toc,image_id=pdf_reader(Target_Folder,pb,pdf_filename,client)
                # text_split_for_gpt,title=decompose_text(text)
                document = self.client.find_data("Papers_info","Paper_name",pb)
                # print(document)
                if document and not self.gpt_Dubug_mode:
                    reply_dic=document.pop()
                    logger.info(f"{th.current_thread().name} Done !!! Exist in DB: {pb},usage {self.Paper_gpt.prompt_tokens+self.Paper_gpt.complete_tokens} tokens, Progress: {self.q_in.qsize()}\{self.job_all}\n")
                else:
                    ################################ GPT REquest
                    if not self.gpt_Dubug_mode:
                        for cc in range(self.regen_times):
                            try:
                                self.Get_openai_GPT(pb,pdf_filename)
                            except:
                                logger.debug(f"{th.current_thread().name} {pb} Format Wrong {cc}, Try to regenerate\n")
                                continue
                    else:
                        self.Get_openai_GPT(pb,pdf_filename)
                        # print(self.reply_dic['organization_name'])
                    # os.system(f"echo {self.reply_dic}")
                    self.client.insert_data("Papers_info","Paper_name",self.reply_dic)

                self.out_lock.acquire()
                self.q_out.put(pb)
                self.q_in_spent.put(self.Paper_gpt.prompt_tokens)
                self.q_out_spent.put(self.Paper_gpt.complete_tokens)

                self.out_lock.release()
                if self.gpt_Dubug_mode:
                    logger.info(f"{th.current_thread().name} Finish GPT Generateion on {pb}")
                ## CLIP
                Func_clip_([pb],self.args)
                if self.gpt_Dubug_mode:
                    logger.info(f"{th.current_thread().name} Finish CLIP Generateion on {pb}")

                logger.info(f"{th.current_thread().name} Insert to DB: {pb},usage {self.Paper_gpt.prompt_tokens+self.Paper_gpt.complete_tokens} tokens, Progress: {self.q_in.qsize()}\{self.job_all}\n")
            else:
                # print(f"{th.current_thread().name} Sleeping {q_in.qsize()}")
                self.client.mysql_close()
                self.in_lock.release()
                if self.terminal.is_set():
                    break

def GPT_Analysis_(config,target_list:list)->None:

    Empty_GPU_Cache()
    CheckGPU()
    gpt_overall_cost=0
    s=time.time()
    #### Get Target_folder
    for Target_Folder in target_list:
        in_,out_,in_spent_,outspent_=Queue(),Queue(),Queue(),Queue()
        in_lock,out_lock,blip_lock=th.Lock(),th.Lock(),th.Lock()
        terminal=th.Event()
        Paper_list=[]
        thread=[]
        gpt_total_cost={}
        generate_tokens,prompt_tokens=0,0
        pub_num=list(map(killblankspace,glob.glob(f"{Target_Folder}/*.pdf")))
        ## Put in queue
        for job in pub_num:
            # in_lock.acquire()
            in_.put(job)
            # in_lock.release()
        ## Parrallel Processing Thread Start
        if pub_num:
            for i in range(config['MainConfig']['thread_size']):
                thread.append(gpt_Worker(Target_Folder,len(pub_num),in_,out_,in_spent_,outspent_,in_lock,out_lock,terminal,config))
                thread[i].start()

        ## pdf_path,json_setting_path,job_all,q_in,q_out,q_in_spent,q_out_spent,in_lock,out_lock,blip_lock,terminal,GPTmodel,gpt_Dubug_mode,clip_Dubug_mode
        else:
            raise ValueError("There is no file in path!!")

        terminal.set()
        logger.info(f"{Target_Folder} Put job : {len(pub_num)}, Thread num: {config['MainConfig']['thread_size']}")
        for i in range(len(pub_num)):
            out_lock.acquire()
            while out_.qsize()==0:
                out_lock.release()
                time.sleep(0.01)
                out_lock.acquire()
            Paper_list.append(out_.get())
            generate_tokens+=outspent_.get()
            prompt_tokens+=in_spent_.get()
            out_lock.release()

        for t in thread:
            t.join()
        ### AI module Serial Thread Join
        gpt_pricing={
            "gpt-3.5-turbo-0125":{"input(1k)":0.0005 ,"output(1k)":0.0015},
            "gpt-4":{"input(1k)":0.03 ,"output(1k)":0.06},
        }
        gpt_total_cost["Project_name"]=Target_Folder.split("\\")[-1]
        gpt_total_cost["GPT_Cost_usd"]=round((prompt_tokens/1000*gpt_pricing[config['MainConfig']['GPTmodel']]["input(1k)"]+generate_tokens/1000*gpt_pricing[config['MainConfig']['GPTmodel']]["output(1k)"]),5)

        logger.info(f"{Target_Folder} GPT Total Cost {gpt_total_cost['GPT_Cost_usd']} US Dollars")

        ## Update Cosr Per Case
        client=mysql_db_client(config)
        client.insert_data("GPT_Cost","Project_name",gpt_total_cost)

        Empty_GPU_Cache()
        if config['MainConfig']['blip_Dubug_mode']:
            Func_blip_(Paper_list,config)

        if make_ppt:
            logger.info(f"PPT in {make_ppt(Target_Folder,Paper_list,client,config)} ")

        logger.info("====== END ======")
        gpt_overall_cost+=gpt_total_cost["GPT_Cost_usd"]
        logger.info(f"Total time : {time.time()-s},GPT Cost : {gpt_overall_cost} US Dollars")
