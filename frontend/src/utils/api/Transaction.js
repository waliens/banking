import Account from './Account';
import Model from './Model';
import moment from 'moment';

export default class Transaction extends Model {
  /** @inheritdoc */
  static get className() {
    return 'transaction';
  }

  async setCategory(id_category) {
    let {data} = await Transaction.backend().put(`${this.uri}/category/${id_category}`);
    this.id_category = data.id_category;
    this.category = data.category;
    return this;
  }

  static async setCategories(new_categories) {
    let {data} = await this.backend().put(`${this.collectionName}/tag`, {'categories': new_categories});
    return data;
  }

  /** @inheritdoc */
  _initProperties() {
    super._initProperties();

    this.id_source = null;
    this.id_dest = null;
    this.when = null;
    this.metadata_ = {};
    this.amount = null;
    this.id_currency = null;
    this.id_category = null;
    this.source = null;
    this.dest = null;
    this.currency = null;
    this.category = null;
  }

  mappers() {
    return {
      when(value) {
        return moment(value).toDate();
      },
      amount(value) {
        return new Number(value);
      },
      dest(value) {
        return value ? new Account(value) : null;
      },
      source(value) {
        return value ? new Account(value) : null;
      },
      is_duplicate_of(value) {
        return value? new Transaction(value) : null;
      }
    }
  }

  async getGroupIds() {
    let {data} = await Model.backend().get(`${this.uri}/account_groups`);
    return new Set(data);
  }

  async markAsNotDuplicate() {
    return await Model.backend().delete(`${this.uri}/duplicate_of`);
  }

  async markAsDuplicate(id_original) {
    let {data} = await Model.backend().put(`${this.uri}/duplicate_of/${id_original}`);
    return data;
  }

  async getCandidateDuplicates(days=7) {
    let {data} = await Model.backend().get(`${this.uri}/duplicate_of/candidates`, {params: {days}});
    return data.map(t => new Transaction(t));
  }

}