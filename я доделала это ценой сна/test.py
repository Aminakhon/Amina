import requests
import time
API_URL = 'http://127.0.0.1:5000/api/'

def create_user_request(name, login, email, password, description, country, phone, isPublic, image):
    return requests.post(
        API_URL + 'registration',
        json={'name': name,
              'login': login,
              'email': email,
              'password':password,
              'description': description,
              'country': country,
              'phone':phone,
              'isPublic': isPublic,
              'image': image
    }
    )

def login_request(login, password):
    return requests.post(
        API_URL + 'sign_in',
        json={'login': login,
              'password':password
    }
    )
def delete_user(id):
    return requests.delete(API_URL + 'delete/' + str(id))

def get_country_request(alpha2):
    return requests.get(API_URL + 'country/' + str(alpha2))

def meprofile_request(token):
    return requests.get(
                        API_URL + 'me/profile',
                        headers={"Authorization": f"Bearer {token}"}
    )
def meprofile_patch(token, new):
    return requests.patch(
                        API_URL + 'me/profile',
                        headers={"Authorization": f"Bearer {token}"},
                        json = new
    )
def get_profile_request(token, login):
    return requests.get(API_URL + 'profiles/' + str(login),
                        headers={"Authorization": f"Bearer {token}"}
                        )

def new_password_change(token, new):
    return requests.post(API_URL + 'me/updatePassword',
                        headers={"Authorization": f"Bearer {token}"},
                        json = {'old_password': 'password', 'new_password':'something'}
                        )
def registration():
    return requests.get(API_URL + 'registration')
def all_countries():
    return requests.get(API_URL + 'countries')

def run_artists_api_tests():
    artist_response23 = create_user_request('name1', 'login1', 'email1', 'password1', 'description1', 'RU', 'phone1', True, 'image1')
    user = create_user_request('name', 'login', 'email', 'password', 'description', 'RU', 'phone', True, 'image')
    assert user.status_code == 200

    print("Artist creation tests passed!")

    # сохраняем id новых артистов
    user_country = user.json().get('country')
    user_name = user.json().get('name')

    # проверяем, что нельзя создать артиста с уже использованным именем
    artist_response = create_user_request('name1', 'login', 'email', 'password', 'description', 'RU', 'phone', True, 'image')
    assert artist_response.status_code == 400
    print("Artist login uniqueness tests passed!")

    # проверяем, что можно получить артиста по alpha2
    artist_response = get_country_request(user_country)
    assert artist_response.status_code == 200
    print("Get country by alpha2 tests passed!")
    user_login = login_request('login', 'password')
    print(user_login.json())
    assert user_login.status_code == 200
    print('Test login passed')
    token = user_login.json()['token']
    profile_response = meprofile_request(token)
    print(profile_response.json())
    assert profile_response.status_code == 200

    new = {'name': 'Lady AntiBug', 'image':'image'}
    time.sleep(1)
    newer = meprofile_patch(token, new)
    print(newer.json())
    assert newer.status_code == 200
    print("Get patch info test passed!")

    time.sleep(1)
    sth = get_profile_request(token, 'login1')
    assert sth.status_code == 200
    print('Find him!')

    time.sleep(1)
    passwords = {'old_password': 'password', 'new_password': 'Sectumsepra'}
    sth2 = new_password_change(token, passwords)
    print(sth2.json())
    assert sth2.status_code == 200
    print('Change password!')

    # проверяем, что можно получить список артистов
    artist_response = all_countries()
    assert artist_response.status_code == 200
    print("Get all artists tests passed!")

    userer = delete_user(1)
    userer2 = delete_user(2)
    assert userer.status_code == 200


    print("Delete artist tests passed!")

    print("All tests passed!")

if __name__ == '__main__':
    run_artists_api_tests()
