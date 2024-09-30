from pytube import YouTube
from pydub import AudioSegment
from flask import Flask, request, url_for, session, redirect
import os #what does os do 
from googleapiclient.discovery import build
import requests
import json
from PIL import Image
from io import BytesIO



class Song:
    #Song Constructor 
    def __init__(self, song_name, album_name, artist_name, song_url=None, playlist=None, image=None, video=False):
        """
        Initializes an object of the Song class.

        Args:
            song_name (str): The name of the song.
            album_name (str): The name of the album.
            artist_name (str): The name of the artist.
            song_url (str, optional): The URL of the song on YouTube. Default is None.
            playlist (str, optional): The name of the playlist the song belongs to. Default is None.
            image (str, optional): The URL of the song's image. Default is None.
            video (bool, optional): A flag indicating if the song is a video. Default is False.

        Returns:
            None

        Summary:
        The __init__ method initializes an object of the Song class. It sets the attributes of the object based on the input parameters, stores the object's data in a JSON file, searches for the song on YouTube, and downloads and saves the song's image.

        Example Usage:
        song = Song(song_name, album_name, artist_name, song_url, playlist, image, video)

        This code initializes a Song object with the given parameters. The song_name, album_name, and artist_name are required parameters, while the song_url, playlist, image, and video are optional parameters. The object is then stored in the song variable.
        """

        self.artist_name = str(artist_name)
        self.song_title = str(song_name)
        self.album_name = str(album_name)
        self.song_url = song_url
        self.playlist = playlist
        self.video = video
        self.image_location = f'images/{self.album_name}.jpeg'

        #spotify image url
        self.image_url = image

        self.store_data_to_json('song.json')

        #grabs youtube link to store in class
        self.youtube_search()

        self.image = self.download_image_and_save(self.image_url, self.image_location, self.image_location, max_retries=3) # images/{self.album_name}



    def youtube_MP3(self):
        """
        Downloads a YouTube video as an MP3 file.

        Inputs:
        - self.song_url (str): The URL of the YouTube video.
        Outputs:
        - None
        
        Flow:
        1. Create a `YouTube` object using the `song_url`.
        2. Filter the available streams to get the audio stream.
        3. Determine the destination folder based on whether the song belongs to a playlist or not.
        4. Download the audio stream to the destination folder.
        5. Rename the downloaded file to have a `.mp3` extension.
        6. Convert the downloaded file to an MP3 file format.
        7. Add tags such as album and artist information to the MP3 file.
        8. Remove the original downloaded file.
        9. Print a success message.
        """

        print("\nyoutube_MP3 called\n")

        print("url input: ", self.song_url)
        # url input from user
        yt = YouTube(self.song_url) 

        print("extract audio")
        # extract only audio
        audio = yt.streams.filter(only_audio=True).first()

        #Stores Tracks in 'Tracks folder
        if self.playlist == None:
            destination = "/Ben's MacBook Pro/Macintosh HD/Users/benthomas/Music/Music/Media/Tracks"
    
        #Stores all songs from same playlist in the same folder
        else: 
            destination = "test"#f"/Ben's MacBook Pro/Macintosh HD/Users/benthomas/Music/Music/Media/{str(self.playlist)}"

        #Possible Locations: Ben's MacBook Pro/Macintosh HD/Users/benthomas/Music/Music/Media

        # download the file
        print("start download")
        max_retries = 10
        retries = 0
        while retries < max_retries:
            try:
                out_file = audio.download(output_path=destination, timeout=30)
                break  # Break out of the loop if download is successful
            except Exception as e:
                retries += 1
                print(f"Error downloading: {e}: retries: {retries}")
            #creates a list of songs that could not be downloaded
            if max_retries == retries:
                print("song not downloaded: ", str(self.song_title))
                return str(self.song_title)
    
        print("file downloaded")

        #Following code utlized to create a playable mp4
        #convert to MP3
        #renames audiofile:
        print("file renamed")
        base, ext = os.path.splitext(out_file)
        new_file = base + '.mp3'
        #from_file turns out_file into AudioSegment object: .export: converts out_file into mp3 and renames it new_file
        AudioSegment.from_file(out_file).export(new_file, format="mp3", tags={"album": self.album_name, "artist": self.artist_name}, cover = self.image_location) 

    
        # remove the original file
        os.remove(out_file)

        # result of success
        print(yt.title + " has been successfully downloaded and converted to MP3.")
        


    def __str__(self):
        """
        Prints a strings that tells the user the song name, artist, song id, and release year 
        Inputs: self  
        Outputs: A string
        """
        return  ("Song name: %s, Artist name: %s, Playlist name: %s, Image URL: %s, Song URL: %s"
                 %(self.song_title, self.artist_name, self.playlist, self.image_url, self.song_url, ))





    def youtube_search(self):
        print("\nyoutube_search called\n")  
        """
        Perform a search on YouTube using a given list of search queries and return a list of video links.
        Args:
            search_query (list): A list of Song objects representing the search queries.
        Returns:
            list: A list of video links corresponding to the search queries.

        Bugs: this function no longer runs because I exceeded by quota: I get 10,000 queries per day in just a few runs I am at 10,200
            - why is my project requiring so many queries, later test how much a single run uses. It should be roughly 20
        """ 
        api_key = 'AIzaSyBIWffaEwhNz7s4QyIfBK68ASJ-zu4LpNQ'

        youtube = build('youtube', 'v3', developerKey=api_key)

        search_string = f'{self.song_title} by {self.artist_name} '

        search_response = youtube.search().list(part = 'id', q = search_string, type='video', maxResults = 1).execute()

        video_id =search_response['items'][0]['id']['videoId'] 

        self.song_url = f'https://www.youtube.com/watch?v={video_id}'


    def store_data_to_json(self, filename):
        """
        Store the data of a song object in a JSON file.
        Args:
            filename (str): The name of the JSON file to store the data.
        Returns:
            None
        Example Usage:
            song = Song(song_name, album_name, artist_name, song_url, playlist, image)
            song.store_data_to_json('song.json')
        """
        print("\nstore_data_to_json called\n")
        # Create a dictionary with the provided data
        song_data = {
            'song': self.song_title,
            'artist': self.artist_name,
            'data': str(self.image_url)
        }

        # Serialize the dictionary to JSON format
        json_data = json.dumps(song_data, indent=2)

        # Write the JSON data to the specified file
        with open(filename, 'w') as file:
            file.write(json_data)


    def download_image_and_save(self, image_url, save_path, filename, max_retries=3):
        """
        Download an image from a given URL and save it as a JPEG file.
        Args:
            image_url (str): The URL of the image to be downloaded.
            save_path (str): The path where the image will be saved.
            filename (str): The name of the image file.
            max_retries (int, optional): 
            The maximum number of retries in case of download failure. Defaults to 3.
        Returns:
            None
        Raises:
            requests.exceptions.RequestException: If there is an error downloading the image.
        Example:
            song = Song(song_name, album_name, artist_name, song_url, playlist, image)
            song.download_image_and_save(image_url, save_path, filename)
        """
        try:
            # Send a GET request to the URL
            response = requests.get(image_url)
            response.raise_for_status()  # Raise an exception for bad responses

            # Open the image using PIL
            img = Image.open(BytesIO(response.content))

            # Save the image as a JPEG file
            img.save(save_path, 'JPEG')
            print(f"Image downloaded and saved as {save_path}")

        except requests.exceptions.RequestException as e:
            print(f"Error downloading image: {e}")


        
        