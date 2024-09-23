# LLM-Powered Paper Summarization System
For Innolux Paper Summerization Project
```
D:\WEB_PAPER
├─backend
│  ├─app
│  │  ├─assets
│  │  └─lib
│  │      ├─CLIP
│  │      │  ├─clip
│  │      │  │  └─__pycache__
│  │      │  ├─data
│  │      │  ├─notebooks
│  │      │  └─tests
│  │      ├─config
│  │      └─__pycache__
│  └─__pycache__
└─log
```

### Docker Build
- Use Docker compose to build the env
```yaml
Docker compose up
```

## GPT_analysis
```
GPT_Analysis_ is the main function to generate the GPT analysis for the target_list
Args:
    config (dict): The configuration dictionary
    target_list (list): The list of target folders path to analyze
Steps:
    1. Save all the path into the queue
    2. For each therads:
        a. Get the path from the queue
        b. Read the pdf file (utilzed.py/pdf_reader)
        c. Save the image description into the database (mysql_class.py/mysql_db_client.py)
        d. Generate the GPT analysis (OpenAI_GPT_class.py/openai_GPT)
        e. Calculate the Image text similarity (CLIP_Image_text_Similarty.py/Func_clip_)
        f. Generate the Image description (BLIP_image_Description.py/Func_blip_)
        e. Save the GPT analysis into the database (mysql_class.py/mysql_db_client.py)
    3. Generate the PPT (ppt_maker.py/make_ppt)
```

