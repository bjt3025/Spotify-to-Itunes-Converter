import spotipy
from song import Song 
from spotipy.oauth2 import SpotifyOAuth
import time
from flask import Flask, request, url_for, session, redirect, render_template
from pprint import pprint
from googleapiclient.discovery import build
import json



app = Flask(__name__)

app.config['Session_cookie_name'] = 'spotify_cookie'
app.secret_key = 'syedis'
TOKEN_INFO = 'TOKEN_INFO' 

@app.route('/')
def login(): 
    auth_url = create_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirect_page():
    session.clear()
    code =request.args.get('code')
    token_info = create_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('spotify_MP3', _external = True)) #what is 'save_discover_weekly' refering to # changed to spotify_MP3


@app.route('/saveDiscoverWeekly')
def spotify_MP3():
    try: 
        token_info = get_token()
    except: 
        print("user not logged in")
        return redirect('/')
    
    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])

    #-------Givens----------
    songs_not_downloaded = []

    #asks user if they would like to upload a JSON file to be converted to music 
    filename = input("would you like to download songs from a JSON file: (if so type out filename: ")     
    ext = filename.split(".")

    #Uploads users JSON file and turns it into a song 
    if ext[1] == "JSON":
       song_list = JSON_MP3(filename)
    
    #creates a list of songs to dowload
    else: 
        song_list = song_info_recorder(sp)

    #calls function that downloads songs
    for item in song_list:
        song = item.youtube_MP3()
        
        #creates a list of the songs that were not downloaded properly
        if song != None: 
            songs_not_downloaded.append(item)
            print("song not downloaded: ", item)
        
        #returns name of song correctly downloaded 
        else: 
            print("song downloaded: ", item)
    
    #user decides if they would like to attempt to redownload songs: turn into function 
    redownload(songs_not_downloaded)
    
    return song_list   

def JSON_MP3(filename):
    """
    Summary: Turns a JSON file into a list of song objects 
    """
    print("JSON_MP3 called")
    song_list = []

    #gives playlist folder a name 
    playlist_name, ext = filename.split(".")

    #creates a JSON file that can be read as a dictionary 
    with open(filename, 'r') as file:
        JSON_data = json.load(file)

    #iterates through JSON_data and creates song object 
    image_url = JSON_data['cover'] #cover image 
    artist_name = JSON_data['artist'] 
    #grabs each album 
    for album in JSON_data['albums']:
        album_name = album['album']
        print(f"Album: {album_name}")
        #grab each song in each album 
        for song in album['songs']:
            print("song (location of error)", song)
            song_name = song
            song_list.append(Song(song_name, album_name, artist_name, image = image_url, playlist = playlist_name))
            print("Added to Song_list:", Song(song_name, album_name, artist_name, image = image_url, playlist = playlist_name))

    return song_list
   
        
def redownload(songs_not_downloaded):
    """
    Summary: Allows user option to attempt to redownload unsuccessfully downloaded songs 
    
    Param:songs_not_downloaded: list of song objects

    returns: None
    """
    if len(songs_not_downloaded) > 0:
        redownload_songs = input(f"{len(songs_not_downloaded)} songs were not correctly downloaded. Would you like to try again:(yes/no): ")
           
        if redownload_songs == "yes":
            # attempts to download song
            for item in songs_not_downloaded:
                song = item.youtube_MP3()
                
                if song != None: 
                    print("song not downloaded: ", item)
                
                #removes songs that get downloaded 
                else:
                    songs_not_downloaded.remove(item)
                    print("song downloaded: ", item)
            redownload(songs_not_downloaded)
    else:
        return 


#takes my song data and stores song_names, album_names, artist_name in lists 
def song_info_recorder(sp):
    """
    Summary: takes song data and stores song_names, album_names, artist_name in a list

    Called by: 
    spotify_MP3()

    Functions called:
    playlist_chooser()
    interative_song_info_recorder(playlist_name, saved_tracks) 
    
    Param: sp: spotipy object

    returns: song_list: list of song objects
    """
    print("\nsong_info_recorder called\n")
    #------Given----------
    saved_tracks = []
    song_list = [] 
    offset = 0
    #decides how many songs are grabbed
    limit = 50 # I believe 50 is the max
    playlist_default_name = None
     
    #----input-----
    music_download = input('Do you want to download a track or playlist: ')

    #Download a playlisy/playlists 
    if music_download == 'playlist':
        desired_playlist_name, desired_playlist_id, all_playlist, multiple_playlist, playlist_dict = playlist_chooser(sp)

        #Download every playlist
        if all_playlist == True:

            for playlist_name, ID in playlist_dict.items():
                
                #grabs all tracks from playlist
                saved_tracks = sp.playlist_items(playlist_id = ID, limit=limit)["items"]

                #concatenates all the songs in all the playlists
                song_list += interative_song_info_recorder(playlist_name, saved_tracks)
            
            return song_list
        
        #Download multiple playlist
        elif multiple_playlist == True:
            
            for playlist_name, ID in playlist_dict.items():
                
                #grabs all tracks from playlist
                if ID is not None:
                    saved_tracks = sp.playlist_items(playlist_id = ID, limit=limit)["items"]
                else:
                    # Handle the case where ID is None
                    print("Playlist ID is None. Cannot retrieve playlist items.")

                #concatenates all the songs in all the playlists
                song_list += interative_song_info_recorder(playlist_name, saved_tracks)
            
            return song_list 

    
        #Download one playlist    
        else:
            saved_tracks = sp.playlist_items(playlist_id = desired_playlist_id, limit=limit)["items"]
            
            song_list = interative_song_info_recorder(desired_playlist_name, saved_tracks)

            return song_list
    

    #Downloads all Tracks        
    else:
        saved_tracks = sp.current_user_saved_tracks(offset = offset, limit = limit)["items"]

        song_list = interative_song_info_recorder(playlist_default_name, saved_tracks)

        return song_list

    
   
def interative_song_info_recorder(playlist_name, saved_tracks):
    """
    Summary: iterates through "saved song" and creates song objects out of each song 

    Called by: 
    song_info_recorder

    Functions called:
    None
    
    Param: playlist_name: used to identify playlist name
    Param: saved_tracks: list of all the song you want as JSON objects

    returns: song_list: list of song objects
    """
    print("\ninterative_song_info_recorder called\n")
    
    song_list = []
    count = 0
    offset = 0
    limit = 10 

    #iterates through list until all crucial song info is stored in song class
    while True:
        count += 1

        if count == 2: #not saved_tracks:
            break
        
        print("length of saved tracks",len(saved_tracks))
        for items in saved_tracks:

            images_url = items['track']['album']['images'][0]['url']   
            song_name = items["track"]["name"]
            album_name = items["track"]["album"]["name"]
            release_date = items["track"]["album"]["release_date"]
            artist_name = items["track"]["album"]["artists"][0]["name"] # only includes leading artist this may be important later

            song_list.append(Song(song_name, album_name, artist_name, image = images_url, playlist = playlist_name))
            print(song_name)
        
        #offset += limit

    return song_list

def playlist_chooser(sp):
    """
    Summary: let's user pick whether they want to download their songs/a playlist/multiple playlist/all playlists 

    Called by: 
    song_info_recorder

    Functions called:
    None
    
    Param: sp: spotipy object

    returns: desired_playlist_name, desired_playlist_id, all_playlist: bool, multiple_playlist: bool, playlist_dict
    """
    print("\nplaylist_chooser called\n")
    #------Given----------
    #stores song name and ID for all songs 
    playlist_dict = {}
    #initiates variable 
    desired_playlist_name = None
    #dictionary for when user wants songs from a select few playlists
    multiple_playlist_dict = {}
    
    playlists = sp.current_user_playlists()['items'] #grab a JSON filled with info about each playlist
    print("playlists")
    pprint(playlists)

    featured_playlists = sp.featured_playlists()['playlists']['items'] #grab a JSON filled with info about each featured playlist
    print("featured")
    pprint(featured_playlists)

    #grabs each playlist from your playlists
    print("\nYOUR PLAYLISTS!\n")
    for item in playlists:

        playlist_name = item['name']
        playlist_id = item['id']
        
        #appends playlist_name and playlist_id to dictionary object
        playlist_dict[playlist_name] = playlist_id

        print(f"{item['name']}: Description: {item['description']}")
    
    #grabs each playlist from featured playlists
    print("\nFEATURED PLAYLISTS!\n")
    for item in featured_playlists:
        playlist_name = item['name']
        playlist_id = item['id']
        
        #appends playlist_name and playlist_id to dictionary object
        playlist_dict[playlist_name] = playlist_id

        print(f"{item['name']}: Description: {item['description']}")

        
    desired_playlist_name = input('What playlist do you wanna download: option(all/multiple): ')

    if desired_playlist_name == 'all': #when user wants to download all playlists
        return None, None, True, False, playlist_dict
    
    #returns a dictionary for specific chosen playlists
    elif desired_playlist_name == 'multiple':
        multiple_playlist_list = input('What playlists: split playlists with "/": ').split('/')#splits inputted songs 
        
        #iterates through choosen playlists and creates dictionary of their playlist name and ID's
        for playlist_name in multiple_playlist_list:
            playlist_id = playlist_dict.get(playlist_name)

            multiple_playlist_dict[playlist_name] = playlist_id
        
        return None, None, False, True, multiple_playlist_dict
     
    else:
        desired_playlist_id = playlist_dict.get(desired_playlist_name)

        return desired_playlist_name, desired_playlist_id, False, False, playlist_dict


def create_playlist(sp, user_id):
    #not used
    print(sp.current_user_playlists())
    new_playlist = sp.user_playlist_create(user_id,'Python Playlist', True)
    return sp.current_user_playlists()


def get_token():
    """
    summary: gets oauth token and refreshed token if it is expired 

    called by: 
    Spotify_MP3
    """
    token_info = session.get(TOKEN_INFO, None)
    if not token_info: #code is written in a strange way, try rewriting something more intuitive
        redirect(url_for('login', _external=False))
    now = int(time.time())
    #refreshes token if it expires 
    is_expired = token_info['expires_at'] - now < 60 
    if(is_expired): 
        spotify_oauth = create_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

def create_oauth(): 
    """
    Creates oauth token 
    """
    return SpotifyOAuth(client_id = '5fc24360db234d139419a850b6251525', 
                        client_secret = '82b0b5ce4a21448e8ec53c2230cb182b', #client_ID and secret found in app
                        redirect_uri = url_for('redirect_page', _external=True), # I do not really understand this line
                        scope = 'user-library-read playlist-modify-public playlist-modify-private') #scope is foundin api info this should give us everything we need 


app.run(debug=True)
