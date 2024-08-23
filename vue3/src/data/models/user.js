import Model from './model';

export default class User extends Model {
  /** @inheritdoc */
  _init_properties() {
    super._init_properties();
    this.username = null;
    this.password = null;
  }
}