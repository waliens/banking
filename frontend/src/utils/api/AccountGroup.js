import Model from './Model';

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
    this.accounts = null;
  }
}