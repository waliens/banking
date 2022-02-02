//import Account from './Account';
import Model from './Model';
import axios from 'axios';

export default class AccountGroup extends Model {
  /** @inheritdoc */
  static get className() {
    return 'account_group';
  }

  /** @inheritdoc */
  _initProperties() {
    super._initProperties();

    this.name = null;
    this.description = null;
    this.accounts = [];
  }

  static async fetchGroups() {
    let {data} = await axios.get(`account/groups`);
    return data;
  }

  async getIncomesExpensesStats(year, month) {
    let {data} = await axios.get(`${this.uri}/stats/incomeexpense`, { params: {year, month} });
    return data;
  }
}