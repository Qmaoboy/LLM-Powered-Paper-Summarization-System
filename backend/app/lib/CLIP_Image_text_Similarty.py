import threading as th
from CLIP import clip
import re,torch
from tqdm import tqdm
from utilized import *
from mysql_class import mysql_db_client
from PIL import Image
from io import BytesIO
device = "cuda" if torch.cuda.is_available() else "cpu"

def Func_clip_(Paper_List:list,args):
    ## Check GPT_memory
    client=mysql_db_client(args)
    # ii=tqdm(Paper_List,leave=False)
    for key in Paper_List:
        result=client.find_data("Papers_info","Paper_name",key)
        if result:
            for sql_result in result:
                if sql_result['Status'] is not None:
                    if int(sql_result['Status'])>=2 and not args['MainConfig']['clip_Dubug_mode']:
                        # print(f"{th.current_thread().name}_{sql_result['Paper_name']} Status = 1, Skip CLIP")
                        continue
                    else:
                        clipmodel, clippreprocess = clip.load("ViT-B/32", device=device)
                        Image_File = client.find_data("Image_Files","Paper_name",key)
                        if not Image_File:
                            print(f"{th.current_thread().name}_{key} Not Found in Mysql Image_Files Table")
                        else:
                            for image_id in Image_File:
                                image_bytes=image_id["Image_Byte_File"]
                                img=image_id["Image_id"]
                                image= Image.open(BytesIO(image_bytes))
                                text=Concate_list_dic(sql_result["keypoints"],False)
                                image_pre = clippreprocess(image).unsqueeze(0).to(device)
                                text_pre = clip.tokenize([text], context_length=77, truncate=True).to(device)
                                with torch.no_grad():
                                    image_features = clipmodel.encode_image(image_pre)
                                    text_features = clipmodel.encode_text(text_pre)
                                    # print(text)
                                    logits_per_image, logits_per_text = clipmodel(image_pre, text_pre)
                                    probs = logits_per_image.softmax(dim=-1).cpu().numpy()
                                    sql_result["Logit_per_image"][img]=logits_per_image.item()
                                    ##ii.set_postfix_str(f"Description: {description}")
                            sql_result['Represent_image']=sorted(sql_result["Logit_per_image"])[:5]
                            sql_result['Status']=2
                            client.insert_data("Papers_info","Paper_name",sql_result)
                else:
                    print(f"{th.current_thread().name}_{key} Status None")
        else:
            print(f"{th.current_thread().name}_{key} Not Found in Mysql Papers_info Table")
