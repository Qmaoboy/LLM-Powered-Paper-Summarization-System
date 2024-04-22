from transformers import Blip2ForConditionalGeneration,Blip2Processor
import torch,os
device = "cuda" if torch.cuda.is_available() else "cpu"
from mysql_class import mysql_db_client
from utilized import *
from tqdm import tqdm
from io import BytesIO
from PIL import Image

BLIPprocessor=None
BLIPmodel=None

def BLIP2_imagetoprompt(image,text_prompt):

    if image.size[0] >50 and image.size[1] >50:
        inputs = BLIPprocessor(images=image, text=text_prompt,return_tensors="pt").to(device, torch.float16)
        generated_ids = BLIPmodel.generate(**inputs,
                                           max_length = 100,
                                        #    max_new_tokens=100,
                                           temperature=1,  # 适当调整温度值
                                           top_k=50,         # 适当调整 top_k 值
                                           top_p=0.3,# 适当调整 top_p 值
                                           do_sample=True,
                                           )
        generated_text = BLIPprocessor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        return generated_text
    else:
        # raise ValueError(BLIPprocessor(image,return_tensors="pt").to(device, torch.float16))
        return ""

def Func_blip_(Paper_List:list,args):
    ## Check GPT_memory
    global BLIPmodel,BLIPprocessor
    client=mysql_db_client(args)
    ii=tqdm(Paper_List,leave=False)
    for key in ii:
        ii.update()
        result=client.find_data("Papers_info","Paper_name",key)
        if result:
            for sql_result in result:
                if sql_result['Status'] is not None:
                    if int(sql_result['Status']) >=3 and not args['MainConfig']['clip_Dubug_mode']:
                        ii.set_description_str(f"{sql_result['Paper_name']} Status =2")
                        continue
                    elif int(sql_result['Status']) ==2:
                        if not client.check_exist_one("Image_Files","Paper_name",key):
                            ii.set_description_str(f"{sql_result['Paper_name']} Not Found in Mysql Image_Files Table")
                        else:
                            ### Load BLIP model
                            if BLIPmodel is None and BLIPprocessor is None:
                                meminfo=CheckGPU()
                                if meminfo.free < 8895725568 :
                                    ii.set_description_str(f"GPU Memory Check Fail, please Kill the proecess for free GPU Memory")
                                    os._exit(0)
                                ii.set_description_str(f"GPU Memory Check Pass, Start Loading Pretrained Model, pls wait for few minutes ... ... XD")
                                BLIPmodel = Blip2ForConditionalGeneration.from_pretrained("Salesforce/blip2-opt-2.7b", torch_dtype=torch.float16).to(device)
                                ii.set_description_str(f"Loading BLIPmodel Success")
                                BLIPprocessor=Blip2Processor.from_pretrained("Salesforce/blip2-opt-2.7b")
                                ii.set_description_str(f"Loading BLIPprocessor Success")
                                CheckGPU()

                            for image_id in sql_result['Represent_image']:
                                image_info=client.find_data("Image_Files","Image_id",image_id)
                                if image_info:
                                    image_id_data=image_info.pop()
                                    image_bytes=image_id_data["Image_Byte_File"]
                                    image= Image.open(BytesIO(image_bytes))
                                    prompt=f"Question: What is the keypoint of this picture? Answer:"
                                    description=BLIP2_imagetoprompt(image,prompt)
                                    sql_result["image_Description"][image_id]=description
                                    ii.set_description_str(f"BLIP_{sql_result['Paper_name']}_Paper ID: {sql_result['id']}_image ID: {image_id_data['id']}_{image_id}")
                            sql_result['Status']=3

                            client.insert_data("Papers_info","Paper_name",sql_result)
                    else:
                        ii.set_description_str(f"{sql_result['Paper_name']} Status =0 , Not Yet Finish CLIP")
                else:
                    ii.set_description_str(f"{key} Status None")
        else:
            ii.set_description_str(f"{key} Not Found in Mysql Papers_info Table")
    print(f"BLIP Task Finish")
