import os
import sys
import time
import pandas
import requests
import argparse
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

global args
global session

URL = "http://judge.nccucs.org/"
TIME_OFFSET = timedelta(hours=1,minutes=45)
login_data = {'Account':'',"UserPasswd":''}

def process_options():
    global args

    parser = argparse.ArgumentParser(description='Get data from online judge')
    parser.add_argument('-p', '--pid', type=str, required=True, help='Problem ID')
    parser.add_argument('-d', '--dead_line', type=str, default='', help='Submit dead line, format: YYYY-MM-DD HH:MM')
    parser.add_argument('-code', '--download_code', action='store_true', help='Download code from online judge')
    parser.add_argument('-ac', '--account', type=str, default='', help='Account')
    parser.add_argument('-pwd', '--password', type=str, default='', help='Password')
    parser.add_argument('-o', '--output', type=str, default='', help='Output folder')

    args = parser.parse_args()

    if args.output == '':
        args.output = args.pid

    if not is_time_formate(args.dead_line) and args.dead_line != '':
        print("Dead line format is not correct.\n")
        sys.exit(1)

    if login_data['Account']=='' and login_data['UserPasswd']=='':
        login_data['Account'] = args.account
        login_data['UserPasswd'] = args.password

    if not os.path.exists(args.output):
        os.mkdir(args.output)
    else:
        print("output allready exists.")
        sys.exit(1)


def final_page(res):
    tag = ".content_individual p a"
    soup = BeautifulSoup( res.text, "lxml" )
    link = []
    for drink in soup.select('{}'.format(tag)):
        link.append( drink )
    if len(link) == 0:
        return 0
    else:
        parsed_url = urlparse( link[-1].attrs["href"] )
        return int(parse_qs(parsed_url.query)["page"][0])

def is_time_formate(t):
    try:
        datetime.strptime( t, "%Y-%m-%d %H:%M" )
        return True
    except ValueError:
        return False

def judge_df(url):
    df = None
    res = session.get( url )
    cur_final_page = final_page(res)
    if cur_final_page!=0:
        for i in range( 1, final_page(res) + 1 ):
            cur_url = url + "&page=" + str(i)
            cur_df =  pandas.read_html( cur_url, header=0 )[0]
            if df is None:
                df = cur_df
            else:
                df = df.append(cur_df)
        df = df[df['Code']=='C'].reset_index( drop=True )
    return df

def judge_score(p_url, dead_line, output):

    df = None
    # df = judge_df(p_url)
    for status in ["AC","WA","TLE","MLE","OLE","RE"]:
        cur_df = judge_df(p_url + "&status=" + status )
        if df is None:
            df = cur_df
        else:
            df = df.append(cur_df)

    df = df.reset_index( drop=True )
    df = df[df['User'].str.contains('nccucs')]
    df['Time'] = df['Time'].apply( lambda x: datetime.strptime( x, "%Y-%m-%d %H:%M" ) + TIME_OFFSET )
    df['status'] = df['Result'].apply( lambda x: x.split(' ')[0] )
    df['score'] = df.apply( lambda x: 100 if x.status=="AC" else int(x.Result.split(":")[-1].replace(")","")), axis=1 )

    # Save raw data
    df.to_csv( output + '/raw.csv' )

    if dead_line != '':
        df = df[ df['Time'] < datetime.strptime( dead_line, "%Y-%m-%d %H:%M" ) ]

    df = df.sort_values( ['score','Time'], ascending=[0,0] ).reset_index( drop=True )
    df = df.drop_duplicates('User').reset_index( drop=True )
    df['User'] = df['User'].apply( lambda x: x.replace('nccucs','') )

    df.sort_values( ['User'] ).loc[:,['User','score']].to_csv( output + '/results.csv', index=False, header=False )

def judge_code(p_url, dead_line, output):
    df = judge_df( p_url ).reset_index( drop=True )
    df = df[df['User'].str.contains('nccucs')]
    df['Time'] = df['Time'].apply( lambda x: datetime.strptime( x, "%Y-%m-%d %H:%M" ) + TIME_OFFSET )

    if dead_line != '':
        df = df[ df['Time'] < datetime.strptime( dead_line, "%Y-%m-%d %H:%M" ) ]

    df = df.sort_values( ['Time'], ascending=[0] ).reset_index( drop=True )
    df = df.drop_duplicates('User').reset_index( drop=True )
    df['User'] = df['User'].apply( lambda x: x.replace('nccucs','') )
    df['code_url'] = df['ID'].apply( lambda x: URL + "ShowCode?solutionid=" + str(x) )
    download_code(df, output + '/code')

def download_code(url_df, output):
    if not os.path.exists(output):
        os.mkdir(output)
    for i in range( 0, len(url_df) ):
        res = session.get( url_df.loc[ i, 'code_url'] )
        soup = BeautifulSoup( res.content, "html5lib" )
        code = soup.select('textarea')
        with open( output + '/' + url_df.loc[ i, 'User'] + '.c', 'w') as f:
            f.write(code[0].text)

def main():
    global session

    process_options()

    session = requests.session()

    try:
        if args.download_code:
            if login_data['Account']!='' and login_data['UserPasswd']!='':
                session.post( URL + "Login", login_data )
                judge_code(URL + "RealtimeStatus?problemid=" + args.pid, args.dead_line, args.output)
            else:
                print("Because login_data is empty, only download score.\n")
        judge_score(URL + "RealtimeStatus?problemid=" + args.pid, args.dead_line, args.output)

    except ValueError:
        print( "Worng Problem ID\n" )
        sys.exit(1)

if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s mins ---" % round(float((time.time() - start_time))/60, 2))
