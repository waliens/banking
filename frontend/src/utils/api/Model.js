import axios from 'axios';
import qs from 'qs';
import constants from '../constants';

export default class Model {

  /**
   * @param {Object} [props]    Object containing the properties of the object to set
   */
  constructor(props) {
    if (new.target === Model) {
      throw new Error('Model is an abstract class and cannot be constructed directly.');
    }
    this._initProperties();
    this.populate(props);
  }

  static backend() {
    let instance = axios.create({
      baseURL: constants.BACKEND_BASE_URL
    });

    // refresh token
    instance.interceptors.response.use((response) => response, async function (error) {
      let originalRequest = error.config;
      let refreshToken = window.localStorage.refreshToken;
      if (error.response.status === 401 && !originalRequest._retry && refreshToken) {
        originalRequest._retry = true;
        return await axios.post(
          `${constants.BACKEND_BASE_URL}/refresh`, {}, {
            headers: {
              'Authorization': `Bearer ${refreshToken}`
            }
          }
        ).then(({data}) => {
          window.localStorage.accessToken = data.accessToken;
          let header = 'Bearer ' + data.access_token;
          axios.defaults.headers.common.Authorization = header;
          originalRequest.headers.Authorization = header;
          return instance(originalRequest);
        });
      }
      return Promise.reject(error);
    })

    return instance;
  }

  mappers() {
    return {};
  }

  /**
   * Initialize the properties allowed for current object (the children must override this method to initialize their
   * custom properties)
   */
  _initProperties() {
    this.id = null;
  }

  toString() {
    let str = `[${this.className}] ${this.id}`;
    if(this.name) {
      str += `: ${this.name}`;
    }
    return str;
  }

  /**
   * Clone the object
   *
   * @returns {this} the clone of the object
   */
  clone() {
    return new this.constructor(JSON.parse(JSON.stringify(this)));
  }

  /**
   * Populate the instance with the properties of the provided object
   *
   * @param {Object} props Object containing the properties to set
   */
  populate(props) {
    if(props) {
      for(let key in props) {
        this[key] = this.mapField(key, props[key]);
      }
    }
  }

  /**
   * Map field using on the mappers
   * @param {*} key 
   * @param {*} value 
   * @returns 
   */
  mapField(key, value) {
    let defaultMappers = this.mappers();
    if (defaultMappers[key]) {
      return defaultMappers[key](value);
    } else {
      return value;
    }
  }

  /**
   * Return an object containing only the public properties of the current object
   *
   * @param {Array<string>} forcedProperties The properties to include in the constructed properties object, even
   *  if they are  null
   *
   * @returns {Object} Object with public properties only
   */
  getPublicProperties(forcedProperties=[]) {
    let props = {};
    for(let key in this) {
      let value = this[key];
      if(!key.startsWith('_') || forcedProperties.includes(key)) {
        props[key] = value;
      }
    }
    return props;
  }

  /**
   * @static Fetch an object
   *
   * @param {number} id The identifier of the object to fetch
   *
   * @returns {this} The fetched object
   */
  static async fetch(id) {
    return new this({id}).fetch();
  }

  /**
   * Fetch from database the properties of the model and update the model with those properties
   *
   * @returns {this} The object with fetched properties
   */
  async fetch() {
    if(this.isNew()) {
      throw new Error('Cannot fetch a model with no ID.');
    }

    let {data} = await Model.backend().get(this.uri);

    this.populate(data);
    return this;
  }

  /**
   * Fetch all models
   *
   * @param {Object} params The URL params to use in the request
   *
   * @returns {Array<Model>} The list of all models
   */
  static async fetchAll(params={}) {
    let {data} = await this.backend().get(this.collectionName, {
      params,
      paramsSerializer: params => {
        return qs.stringify(params);
      }
    });
    return data.map(elem => new this(elem));
  }

  /**
   * Count number of entries returned by fetchAll
   * @param {*} params 
   * @returns 
   */
  static async countAll(params={}) {
    let {data} = await this.backend().get(`${this.collectionName}/count`, {
      params,
      paramsSerializer: params => {
        return qs.stringify(params);
      }
    });
    return data.count;
  }

  /**
   * Save the object (if it is new, it is added; otherwise, it is updated)
   *
   * @param {Object} params
   * @param {Array<string>} forcedProperties The properties to include in the constructed properties object, even
   *  if they are  null
   *
   * @returns {this} The saved object, as returned by backend
   */
  async save(params={}, forcedProperties=[]) {
    let data;
    if(this.isNew()) {
      ({data} = await Model.backend().post(this.uri, this.getPublicProperties(forcedProperties), {
        params,
        paramsSerializer: params => {
          return qs.stringify(params);
        }
      }));
    }
    else {
      ({data} = await Model.backend().put(this.uri, this.getPublicProperties(forcedProperties)));
    }
    this.populate(data);
    return this;
  }

  /**
   * @static Delete an object
   *
   * @param {number} id The identifier of the object to delete
   */
  static async delete(id) {
    return new this({id}).delete();
  }

  /**
   * Delete the object
   */
  async delete() {
    if(this.isNew()) {
      throw new Error('Cannot delete a model with no ID.');
    }

    await Model.backend().delete(this.uri);
  }

  /**
   * @returns {boolean} whether or not the object is new (not yet added to the database)
   */
  isNew() {
    return (this.id == null);
  }

  /**
   * @returns {string} API URI to use to perform operations on the object
   */
  get uri() {
    if(this.isNew()) {
      return `${this.className}`;
    }
    else {
      return `${this.className}/${this.id}`;
    }
  }

  /**
   * @abstract
   * @returns {string} The class name of the model used in API endpoints
   */
  static get className() {
    throw new Error('Abstract getter className() not overriden in child.');
    // return this.name.toLowerCase(); not used to allow minification
    // (see https://stackoverflow.com/questions/29310530/get-the-class-name-of-es6-class-instance#39522406)
  }

  get className() {
    return this.constructor.className;
  }

  static get collectionName() {
    return this.className + 's';
  }

  static async uploadFiles(files, path, query={}) {
    let formData = new FormData();
    for( var i = 0; i < files.length; i++ ){
      let file = files[i];
      formData.append('files[' + i + ']', file);
    }
    let headers = { headers: { 'Content-Type': 'multipart/form-data' }, params: query };
    return await this.backend().post(path, formData, headers);
  }
}
