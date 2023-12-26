import Model from './Model';
import { strcurrency, formatAccountNumber } from '@/utils/helpers';
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
    let result = await this.backend().put(this.className + "/merge", {id_repr, id_alias});
    return new Account(result.data);
  }

  async transactions() {
    let result = await Account.backend().get(this.uri + "/transactions");
    return result.data;
  }

  async updateChange(data) {
    let payload = {};
    let doUpdate = false;
    if(hasOwnProperty(data, 'initial') && strcurrency(this.initial).intValue != strcurrency(data.initial).intValue) {
      payload.initial = data.initial;
      doUpdate = true;
    }
    if(hasOwnProperty(data, 'representative') && data.representative.id > 0) {
      payload.id_representative = data.representative.id;
      doUpdate = true;
    }
    if (!doUpdate) {
      return this;
    }
    let result = await Account.backend().put(this.uri, payload);
    return result.data;
  }

  async newAlias({name, number}) {
    let {data} = await Account.backend().post(`${this.uri}/alias`, {'name': name, 'number': number});
    return data;
  }

  formatName(ctx) {
    return Account.formatNameByObj(this, ctx)
  }

  static formatNameByObj(obj, ctx) {
    let formatted = '';
    formatted += obj.name ? obj.name : ctx.$t('undefined');
    formatted += " | ";
    formatted += obj.number ? formatAccountNumber(obj.number) : ctx.$t('undefined');
    return formatted;
  }
}