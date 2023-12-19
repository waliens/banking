import Model from './Model';

export default class Group extends Model {
  /** @inheritdoc */
  static get className() {
    return 'user';
  }

  /** @inheritdoc */
  _initProperties() {
    super._initProperties();

    this.username = null;
  }

  static async login(username, password) {
    let {data} = await this.backend().post("/login", {'password': password, 'username': username});
    return data;
  }

  static async fetchCurrent() {
    let {data} = await this.backend().get('user/current');
    return new this(data);
  }

}