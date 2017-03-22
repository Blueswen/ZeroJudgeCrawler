# Online Judge Crawler
Score and code crawler for [ZeroJudge](http://judge.nccucs.org/)

### Dependencies
1. python 3
3. [pandas](http://pandas.pydata.org/)
4. [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
5. perl

### Usage
Download score
```
python3 main.py -p [problem_id] -d [dead_line] -o [output_folder]
```

Download code:
1. Setting login_data's account and password at main.py
    ```
    python3 main.py -p [problem_id] -d [dead_line] -code -o [output_folder]
    ```
2. Login with args
    ```
    python3 main.py -p [problem_id] -d [dead_line] -code -ac [user_account] -pwd [user_password] -o [output_folder]
    ```

More detail
```
python3 main.py -u
```

Code similarity
```
moss.pl -l c code/*.c
```

### Reference
1. [A System for Detecting Software Plagiarism](http://theory.stanford.edu/~aiken/moss/)
