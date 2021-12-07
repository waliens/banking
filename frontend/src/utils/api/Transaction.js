import Model from './Model';

export default class Transaction extends Model {
  /** @inheritdoc */
  static get className() {
    return 'account';
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