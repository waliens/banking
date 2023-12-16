import Model from './Model';

export default class Transaction extends Model {
  /** @inheritdoc */
  static get className() {
    return 'transaction';
  }

  async setCategory(id_category) {
    let {data} = await this.backend().put(`${this.uri}/category/${id_category}`);
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
    this.metadata_ = null;
    this.amount = null;
    this.id_currency = null;
    this.id_category = null;
    this.source = null;
    this.dest = null;
    this.currency = null;
    this.category = null;
  }
}