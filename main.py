import requests
import base64
import json
import datetime

import config_parser
import save_to_excel

client_id, client_secret, market = config_parser.read_config_file()


class SpotifyClient:

    client_id = None
    client_secret = None

    access_token = None
    token_type = None
    token_expires_in = None
    token_expires_time = None

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def make_auth_token(self):
        auth_data = "{}:{}".format(self.client_id, self.client_secret)
        auth_data_64 = base64.b64encode(auth_data.encode())
        token_url = 'https://accounts.spotify.com/api/token'
        data = {'grant_type': 'client_credentials'}
        headers = {'Authorization': 'Basic {}'.format(auth_data_64.decode())}

        token_post_request = requests.post(token_url, data=data, headers=headers)
        if token_post_request.status_code not in range(200, 300):
            return False
        token_data = token_post_request.json()
        self.access_token = token_data['access_token']
        self.token_type = token_data['token_type']
        self.token_expires_in = token_data['expires_in']
        now = datetime.datetime.now()
        self.token_expires_time = now + datetime.timedelta(seconds=self.token_expires_in)

    def token_is_expired(self):
        now = datetime.datetime.now()
        if self.token_expires_time is None:
            return True
        elif now > self.token_expires_time:
            return True
        else:
            return False

    def get_access_token(self):
        if self.token_is_expired():
            self.make_auth_token()
        return self.access_token

    def make_get_request(self, endpoint, headers, params=None):
        r = requests.get(endpoint, headers=headers, params=params)
        if r.status_code in range(200, 300):
            return r.json()
        else:
            print(r.json())
            return False

    def get_artist(self, artist_id):
        artist_id = artist_id
        endpoint = 'https://api.spotify.com/v1/artists/{}'.format(artist_id)
        access_token = self.get_access_token()
        headers = {'Authorization': "Bearer {}".format(access_token)}
        artist_data = self.make_get_request(endpoint, headers)

        if artist_data:
            artist_name = artist_data['name']
            artist_url = artist_data['external_urls']['spotify']
            return artist_name, artist_url
        else:
            return False

    def get_artist_albums_short(self, artist_id):
        artist_id = artist_id
        artist_name, artist_url = self.get_artist(artist_id)
        print("Search discography for artist {} (id: {}, artist_url: {})".format(artist_name, artist_id, artist_url))
        endpoint = 'https://api.spotify.com/v1/artists/{}/albums'.format(artist_id)
        search_params = {'market': market, 'include_groups': 'album', 'limit': 50}
        access_token = self.get_access_token()
        headers = {'Authorization': "Bearer {}".format(access_token)}
        albums = self.make_get_request(endpoint, headers, search_params)
        albums_total = albums['total']
        print("Find {} albums".format(albums_total))

        dict_of_albums = dict()
        offset = 0

        while len(dict_of_albums) < albums_total:
            offset_search_params = {'market': market, 'include_groups': 'album', 'limit': 50, 'offset': offset}
            albums = self.make_get_request(endpoint, headers, offset_search_params)
            for album in albums['items']:
                album_id = album['id']
                dict_of_albums[album_id] = {}
                dict_of_albums[album_id]['name'] = album['name']
                dict_of_albums[album_id]['release_date'] = album['release_date']
                dict_of_albums[album_id]['total_tracks'] = album['total_tracks']
                dict_of_albums[album_id]['url'] = album['external_urls']['spotify']
            print("Save {} albums".format(len(dict_of_albums)))

            offset += 50

        return dict_of_albums

    def get_album_tracks(self, album_id):
        album_id = album_id
        endpoint = 'https://api.spotify.com/v1/albums/{}/tracks'.format(album_id)
        search_params = {'market': market, 'limit': 50}
        access_token = self.get_access_token()
        headers = {'Authorization': "Bearer {}".format(access_token)}

        tracks = self.make_get_request(endpoint, headers, params=search_params)
        tracks_total = tracks['total']

        dict_of_tracks = {}
        offset = 0
        while len(dict_of_tracks) < tracks_total:
            offset_search_params = {'market': market, 'limit': 50, 'offset': offset}
            tracks = self.make_get_request(endpoint, headers, params=offset_search_params)
            for track in tracks['items']:
                track_id = track['id']
                dict_of_tracks[track_id] = {}
                dict_of_tracks[track_id]['disc_number'] = track['disc_number']
                dict_of_tracks[track_id]['track_number'] = track['track_number']
                dict_of_tracks[track_id]['name'] = track['name']
                dict_of_tracks[track_id]['duration'] = str(datetime.timedelta(milliseconds=track['duration_ms']))
                dict_of_tracks[track_id]['track_url'] = track['external_urls']['spotify']

            offset += 50
        return dict_of_tracks

    def get_artist_albums_full(self, artist_id):
        artist_id = artist_id
        albums = self.get_artist_albums_short(artist_id)

        for album in albums.keys():
            albums[album]['tracks'] = self.get_album_tracks(album)

        return albums


def save_short_data_to_json(data, file_name):
    with open('{}.json'.format(file_name + '_short_discography'), 'w', encoding='utf8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def save_full_data_to_json(data, file_name):
    with open('{}.json'.format(file_name + '_full_discography'), 'w', encoding='utf8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def main():
    spotify = SpotifyClient(client_id, client_secret)

    actor_id = input("Input Spotify ID of the artist: ")

    while not spotify.get_artist(actor_id):
        print("Error! Try again.")
        actor_id = input("Input Spotify ID of the artist: ")

    artist_name, artist_url = spotify.get_artist(actor_id)

    short_list = spotify.get_artist_albums_short(actor_id)
    #save_to_excel.save_short_data_to_excel(artist_name, short_list)
    save_short_data_to_json(short_list, artist_name)

    full_list = spotify.get_artist_albums_full(actor_id)
    save_full_data_to_json(full_list, artist_name)
    save_to_excel.save_full_data_to_excel(artist_name, full_list)


if __name__ == '__main__':
    main()
