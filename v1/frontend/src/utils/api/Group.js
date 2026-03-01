//import Account from './Account';
import Model from './Model';

export default class Group extends Model {
  /** @inheritdoc */
  static get className() {
    return 'account_group';
  }

  /** @inheritdoc */
  _initProperties() {
    super._initProperties();

    this.name = null;
    this.description = null;
    this.account_groups = [];
  }

  static async fetchGroups() {
    let {data} = await this.backend().get(`account/groups`);
    return data;
  }

  async linkTransactions(transactions) {
    let {data} = await Group.backend().put(`${this.uri}/transactions`, {'transactions': transactions});
    return data;
  }

  async unlinkTransactions(transactions) {
    let {data} = await Group.backend().delete(`${this.uri}/transactions`, {data: {'transactions': transactions}});
    return data;
  }

  async getIncomesExpensesStats(year, month) {
    let {data} = await Group.backend().get(`${this.uri}/stats/incomeexpense`, { params: {year, month} });
    return data;
  }

  /**
   * @param {period_from, period_to, id_category, level, unlabeled, income_only} params 
   */
  async getPerCategoryStats(params) {
    let {data} = await Group.backend().get(`${this.uri}/stats/percategory`, { params });
    return data;
  }

  /**
   * @param {period_from, period_to, id_category, level, unlabeled, income_only} params 
   */
  async getPerCategoryMonthlyStats(params) {
    let {data} = await Group.backend().get(`${this.uri}/stats/percategorymonthly`, { params });
    return data;
  }
}