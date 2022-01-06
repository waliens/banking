import Model from './Model';
import axios from 'axios';
import currency from 'currency.js';
import { hasOwnProperty } from '../helpers';

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

  static async merge(id_repr, id_alias) {
    let result = await axios.put(this.className + "/merge", {id_repr, id_alias});
    return new Account(result.data);
  }

  async transactions() {
    let result = await axios.get(this.uri + "/transactions");
    return result.data;
  }

  async updateChange(data) {
    console.log("whaaat");
    let payload = {};
    let doUpdate = false;
    console.log(payload);
    console.log(hasOwnProperty(data, 'initial'));
    console.log(currency(this.initial).intvalue != currency(data.initial).intvalue);
    if(hasOwnProperty(data, 'initial') && currency(this.initial).intValue != currency(data.initial).intValue) {
      console.log("update initial");
      payload.initial = data.initial;
      doUpdate = true;
    }
    if(hasOwnProperty(data, 'representative') && data.representative.id > 0) {
      console.log("update repre");
      payload.id_representative = data.representative.id;
      doUpdate = true;
    }
    if (!doUpdate) {
      return this;
    }
    console.log("before requestsd");
    let result = await axios.put(this.uri, payload);
    return result.data;
  }

  formatName(ctx) {
    return Account.formatNameByObj(this, ctx)
  }

  static formatNameByObj(obj, ctx) {
    let formatted = '';
    formatted += obj.name ? obj.name : ctx.$t('undefined');
    formatted += " | ";
    formatted += obj.number ? obj.number : ctx.$t('undefined');
    return formatted;
  }
}