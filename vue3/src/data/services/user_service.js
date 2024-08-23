import BaseService from "./base"
import User from "@/data/models/user"

export default class UserService extends BaseService {

 /**
   * Abstract getter for resource path prefix.
   * @returns {string} Resource path prefix.
   */
  get resource_prefix() {
    return 'user';
  }

  /**
   * Abstract getter for model class.
   * @returns {Model} Model class.  
   */
  get model_class() {
    return User;
  }

  async fetch_current_user() {
    let {data} = await axios.get('/user');
    return this.model_class()(data);    
  }

  async login(username, password) {
    let {data} = await axios.post('/login', { username, password });
    return data;
  }

  async refresh_token(refresh_token) {
    let {data} = await axios.post('/refresh', {headers: {'Authorization': `Bearer ${refresh_token}`}});
    return data;
  }
} 