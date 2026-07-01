.
├── README.md
├── ask_answer_robot
│   ├── BERT服务配置指南.md
│   ├── clear_data.py
│   ├── data_importer.py
│   ├── import_data.py
│   ├── import_quick_qa.py
│   ├── main.py
│   ├── qa_service.py
│   ├── requirements.txt
│   ├── retrieval_engine.py
│   ├── web_app.py
│   └── 语料库
│       └── 自己下载，太大了放不下.txt
├── gen_tree.py
├── main.py
├── movieanswer
│   ├── Movie-KBQA
│   │   ├── data
│   │   │   ├── import
│   │   │   │   ├── genre.csv
│   │   │   │   ├── movie.csv
│   │   │   │   ├── movie_to_genre.csv
│   │   │   │   ├── person.csv
│   │   │   │   └── person_to_movie.csv
│   │   │   ├── question
│   │   │   │   ├── question_classification.txt
│   │   │   │   ├── vocabulary.txt
│   │   │   │   ├── 【0】评分.txt
│   │   │   │   ├── 【10】某演员出演过哪些类型的电影.txt
│   │   │   │   ├── 【11】演员A和演员B合作了哪些电影.txt
│   │   │   │   ├── 【12】某演员一共演过多少电影.txt
│   │   │   │   ├── 【13】演员出生日期.txt
│   │   │   │   ├── 【1】上映.txt
│   │   │   │   ├── 【2】风格.txt
│   │   │   │   ├── 【3】剧情.txt
│   │   │   │   ├── 【4】某电影有哪些演员出演.txt
│   │   │   │   ├── 【5】演员简介.txt
│   │   │   │   ├── 【6】某演员出演过的类型电影有哪些.txt
│   │   │   │   ├── 【7】某演员演了什么电影.txt
│   │   │   │   ├── 【8】演员参演的电影评分【大于】.txt
│   │   │   │   └── 【9】演员参演的电影评分【小于】.txt
│   │   │   ├── userdict3.txt
│   │   │   └── vocabulary.txt
│   │   └── src
│   │       ├── compose_question_template.py
│   │       ├── data_loader.py
│   │       ├── knowledge_base.py
│   │       ├── main_retrieval.py
│   │       ├── main_service.py
│   │       ├── movie_qa_app.py
│   │       ├── query.py
│   │       ├── query_template.py
│   │       ├── question_classification.py
│   │       ├── question_preprocess.py
│   │       ├── question_template.py
│   │       ├── retrieval_engine.py
│   │       ├── retrieval_service.py
│   │       ├── rule_based_reply.py
│   │       ├── static
│   │       │   ├── css
│   │       │   │   └── style.css
│   │       │   └── js
│   │       │       └── main.js
│   │       ├── templates
│   │       │   ├── movie_qa.html
│   │       │   └── retrieval_chat.html
│   │       ├── text_pos_tagging.py
│   │       └── web_app.py
│   └── requirements.txt
├── outputs
├── project_tree.md
├── requirements.txt
├── start
│   ├── app.py
│   ├── config.py
│   ├── database.py
│   ├── static
│   │   ├── css
│   │   │   └── style.css
│   │   ├── js
│   │   │   ├── admin.js
│   │   │   ├── admin_login.js
│   │   │   ├── login.js
│   │   │   └── register.js
│   │   └── voice
│   │       ├── main.js
│   │       └── style.css
│   └── templates
│       ├── admin.html
│       ├── admin_login.html
│       ├── login.html
│       ├── movie_qa_content.html
│       ├── qa_discussion_content.html
│       ├── qa_robot_content.html
│       ├── register.html
│       ├── voice_assistant.html
│       └── voice_index.html
├── static
│   ├── css
│   │   └── style.css
│   └── js
│       └── main.js
├── templates
│   └── index.html
├── text_similarity
│   ├── README.md
│   ├── __init__.py
│   ├── bm25.py
│   ├── edit_distance.py
│   ├── hamming_distance.py
│   ├── jaccard.py
│   ├── lcs.py
│   ├── loss_functions.py
│   ├── ngram.py
│   ├── ngram_distance.py
│   ├── pairwise.py
│   ├── pointwise.py
│   ├── tfidf.py
│   └── train_pairwise.py
├── text_similarity.zip
├── tree_output.txt
├── uploads
└── voice_assistant
    ├── app.py
    ├── asr.py
    ├── main.py
    ├── movieanswer
    │   └── Movie-KBQA
    │       └── src
    │           └── templates
    ├── outputs
    ├── start
    │   └── static
    │       └── voice
    ├── static
    │   ├── css
    │   │   └── style.css
    │   └── js
    │       └── main.js
    ├── templates
    │   └── index.html
    ├── translator.py
    ├── tts.py
    └── uploads
