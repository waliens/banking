import Model from './Model';
import axios from 'axios';

export default class Account extends Model {
  /** @inheritdoc */
  static get className() {
    return 'account';
  }

  /** @inheritdoc */
  _initProperties() {
    super._initProperties();

    this.number = null;
    this.name = null;
    this.initial = null;
  }

  async transactions() {
    let result = await axios.get(this.uri + "/transactions");
    return result.data;
  }
}