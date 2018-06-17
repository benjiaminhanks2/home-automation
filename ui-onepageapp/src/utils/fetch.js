import Auth from "../utils/auth";
import {API_ENDPOINT} from "../../config"

export const postJson = (path, body, method) => {
    return new Promise((resolve, reject) => {
        doFetch(path, {
            method: method ? method : 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(body)
        }).then(response => {
            if (!response.ok) {
                throw Error(response.statusText);
            }
            return response.text();
        }).then(token => {
            resolve(token);
        }).catch(e => reject(e));
    });
};

export const remove = (path) => {
    return new Promise((resolve, reject) => {
        doFetch(path, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        }).then(response => {
            if (!response.ok) {
                return false;
            }
            return true;
        }).then(token => {
            resolve(token);
        }).catch(e => reject(e));
    });
};

export const getJson = (path) => {
    return new Promise((resolve, reject) => {
        doFetch(path, {
            method: 'GET',
            headers: getAuthHeaders(),
        }).then(response => {
            if (!response.ok) {
                reject(response.statusText);
                return;
            }
            return response.json();
        }).then(token => {
            resolve(token);
        });
    });
};

const getAuthHeaders = () => {
    return {
                'Content-Type': 'application/json',
                'Authorization': `bearer ${Auth.getToken()}`,
            };
};

export const doFetch = (path, request) => {
    return fetch(API_ENDPOINT + path, request);
};