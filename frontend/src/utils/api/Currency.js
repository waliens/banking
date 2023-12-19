import Model from './Model';

export default class Currency extends Model {
  /** @inheritdoc */
  static get className() {
    return 'currency';
  }

  static get collectionName() {
    return 'currencies';
  }

  /** @inheritdoc */
  _initProperties() {
    super._initProperties();

    this.symbol = null;
    this.short_name = null;
    this.long_name = null;
    this.name = null;
  }

  static currency2icon(currency) {
    if (currency.short_name == "EUR") {
      return "euro-sign";
    } else if (currency.short_name == "USD") {
      return "dollar-sign"
    } else if (currency.short_name == "GBP") {
      return "pound-sign";
    } else {
      throw new Error("unknow currency");
    }
  }
}