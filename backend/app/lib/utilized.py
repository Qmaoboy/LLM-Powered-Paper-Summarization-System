import pynvml
import torch,re,os,fitz,gc,threading as th
from io import BytesIO
from PIL import Image
import lib.logger as logger
import datetime
logger = logger.setup_logger(f'log/{datetime.datetime.now().strftime("%Y-%m-%d_%H")}_backend.log')


def Empty_GPU_Cache():
    gc.collect()
    torch.cuda.empty_cache()

def CheckGPU():
    pynvml.nvmlInit()
    cudar = torch.cuda.memory_reserved(0)
    cudaa = torch.cuda.memory_allocated(0)
    hadle=pynvml.nvmlDeviceGetHandleByIndex(0)
    meminfo=pynvml.nvmlDeviceGetMemoryInfo(hadle)
    logger.info(f"The GPU : 0 Total Have :{meminfo.total/(1024**3):.2f} gb , Used : {meminfo.used/(1024**3):.2f} gb , Free : {meminfo.free/(1024**3):.2f} gb")
    return meminfo

def Concate_list_dic(Target_object,split=", "):
    if isinstance(Target_object,list):
            Target_object=f'{split}'.join(Target_object)
    elif isinstance(Target_object,dict):
            if isinstance(Target_object.values(),dict):
                Target_object=f'{split}'.join(Target_object.values().values())
            else:
                Target_object=f'{split}'.join(Target_object.values())
    else:
        Target_object=Target_object
    return Target_object

def calc_image_image_similarity(target, image, device):
    '''Calculate the similarity between different images -> image to image similarity

    target: target image used in CLIP model -> if PIL=False: input image PATH -> str
                                            -> if PIL=True: input PIL Image -> PIL
    image: image used in CLIP model -> if PIL=False: input image PATH -> str
                                    -> if PIL=True: input PIL Image -> PIL
    model: CLIP
    processor: CLIP processor
    PIL: False -> use image PATH as input
        True -> use PIL Image as input
    '''
    if device == "cpu":
        scores = torch.nn.functional.cosine_similarity(target, image).item()
    else:
        scores = torch.nn.functional.cosine_similarity(target, image).item()
    return scores


def killblankspace(old):
    new=re.sub(r"[\s-]+", "_", old)
    if old!=new:
        os.rename(old, new)
    return new

def set_Target_list():
    Target_list=[]
    k=1
    while True:
        try:
            iter =int(input("How many Path do u want to Process ? "))
            break
        except:
            logger.info("Please input number")
    while(iter>0):
        path=input(f"Please input the {k}th Target Folder Direct Path : ").strip().replace('"',"")
        if os.path.exists(path):
            Target_list.append(killblankspace(path))
            iter-=1
            k+=1
        else:
            logger.info(f"{path} not exists")
    return Target_list

def decompose_text(text):
        text_sum=text
        text_split_for_gpt,toekn_num=[text_sum],len(text_sum.split())
        # 為了避免超出ChatGPT 所必須的 Token= 4097 數量，裁切句子分批送入GPT 中。
        # 設定把Text 切割的 Token 大小
        split_size=750 # 1000 tokens for 750 words
        if re.search(r'Abstract',text,re.IGNORECASE):
            title=text[0:re.search(r'Abstract',text,re.IGNORECASE).span()[0]]
        else:
            title=text[:1024]
        if toekn_num > 2000 or True:
            text_split_for_gpt=[text_sum.split()[i*split_size:(i+1)*split_size] for i in range(((toekn_num)//split_size)+1)]

            for word in range(len(text_split_for_gpt)):
                text_split_for_gpt[word]=" ".join(text_split_for_gpt[word])

        return text_split_for_gpt,title

def pdf_reader(pdf_path,pub_num,pdf_filename,client,gpt_Dubug_mode):

        pdf_file_path=os.path.join(pdf_path,f"{pdf_filename}.pdf")
        project_name=pdf_path.split("\\")[-1]
        doc=fitz.open(pdf_file_path)
        text=''
        toc=doc.get_toc()
        image_id=[]
        img_list_total=set()
        if gpt_Dubug_mode:
            logger.info(f"{th.current_thread().name}_{pub_num}_{len(range(doc.page_count))} Pages\n")
        for pg in range(len(doc)):
            page=doc.load_page(pg)
            text+=page.get_text()
            img_list = doc.get_page_images(pg,full=True)
            img_list_total|=set(img_list)
        count=1
        if img_list_total:
            if gpt_Dubug_mode:
                logger.info(f"{th.current_thread().name}_{pub_num}_Total_{len(img_list_total)}_images\n")
            # print(img)
            for img_info in img_list_total:
                    # image_save_path_file=os.path.join(image_pb_path,f"img_{count}.png")
                    pix=fitz.Pixmap(doc, img_info[0])
                    try:
                        if not pix.colorspace.name in (fitz.csGRAY.name, fitz.csRGB.name):
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                    except:
                        pass
                    # pix.save(image_save_path_file)
                    img_bytes = pix.tobytes()

                    image = Image.open(BytesIO(img_bytes))## 開起圖片
                    # image_id[f"img_{count}.png"]=image
                    Image_data={
                            'Project_name':f'{project_name}',## Project_name
                            "Paper_name":f"{pub_num}",
                            "Image_id": f"{pub_num}_Fig_{count}.png",
                            "Image_Byte_File": img_bytes,
                    }
                    client.insert_data("Image_Files","Image_id",Image_data)
                    count+=1

        if gpt_Dubug_mode:
            logger.info(f"{th.current_thread().name}_{pub_num} Image {count} Done")
        doc.close()

        return text,toc,image_id


def News_reader(url:str,client):
    pass
