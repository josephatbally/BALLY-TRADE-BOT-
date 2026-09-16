from pathlib import Path

target = Path("mobile/src/screens/TradesScreen.tsx")
content = target.read_text(encoding="utf-8")

# 1. Update imports
old_import = "import { executeOrder } from '../api/ordersApi';"
new_import = "import { executeOrder, closePosition, closeAllPositions } from '../api/ordersApi';"

if old_import in content:
    content = content.replace(old_import, new_import)

# 2. Update handleExecuteOrder and add close handlers
old_handler = """  // Order execution handler
  const handleExecuteOrder = async () => {
    const lot = parseFloat(lotSize);
    if (isNaN(lot) || lot <= 0) {
      Alert.alert('Invalid Lot', 'Please specify a valid trade volume.');
      return;
    }

    Alert.alert(
      `Confirm ${orderType} Order`,
      `${orderType} ${lot.toFixed(2)} lots of ${selectedSymbol} at market price?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm & Execute',
          style: orderType === 'BUY' ? 'default' : 'destructive',
          onPress: async () => {
            setSubmitting(true);
            try {
              const res = await executeOrder({
                symbol: selectedSymbol,
                action: orderType,
                lot_size: lot,
              });

              if (res && (res.status === 'EXECUTED' || res.order_sent)) {
                Alert.alert('Order Dispatched', res.reason || 'Order submitted to execution pipeline.');
                fetchAllData();
              } else {
                Alert.alert('Execution Gate', res?.reason || 'Order blocked by safety checks.');
              }
            } catch (err: any) {
              Alert.alert('Order Failed', err?.message || 'Network request failed.');
            } finally {
              setSubmitting(false);
            }
          },
        },
      ]
    );
  };"""

new_handler = """  // Order execution handler (accepts direct action to avoid state lag)
  const handleExecuteOrder = async (action: 'BUY' | 'SELL') => {
    setOrderType(action);
    const lot = parseFloat(lotSize);
    if (isNaN(lot) || lot <= 0) {
      Alert.alert('Invalid Lot', 'Please specify a valid trade volume.');
      return;
    }

    Alert.alert(
      `Confirm ${action} Order`,
      `${action} ${lot.toFixed(2)} lots of ${selectedSymbol} at market price?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm & Execute',
          style: action === 'BUY' ? 'default' : 'destructive',
          onPress: async () => {
            setSubmitting(true);
            try {
              const res = await executeOrder({
                symbol: selectedSymbol,
                action: action,
                lot_size: lot,
              });

              if (res && (res.status === 'EXECUTED' || res.order_sent)) {
                Alert.alert('Order Dispatched', res.reason || 'Order submitted to execution pipeline.');
                fetchAllData();
              } else {
                Alert.alert('Execution Gate', res?.reason || 'Order blocked by safety checks.');
              }
            } catch (err: any) {
              Alert.alert('Order Failed', err?.message || 'Network request failed.');
            } finally {
              setSubmitting(false);
            }
          },
        },
      ]
    );
  };

  // Close single position handler
  const handleClosePosition = async (ticket: number, sym: string) => {
    Alert.alert(
      'Close Position',
      `Close position #${ticket} on ${sym}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Close Trade',
          style: 'destructive',
          onPress: async () => {
            setSubmitting(true);
            try {
              const res = await closePosition(ticket);
              if (res && (res.status === 'SUCCESS' || res.closed)) {
                Alert.alert('Trade Closed', `Position #${ticket} has been closed.`);
                fetchAllData();
              } else {
                Alert.alert('Close Error', res?.reason || 'Could not close position.');
              }
            } catch (err: any) {
              Alert.alert('Close Failed', err?.message || 'Network error closing position.');
            } finally {
              setSubmitting(false);
            }
          },
        },
      ]
    );
  };

  // Close all positions handler
  const handleCloseAllPositions = async () => {
    Alert.alert(
      'Close All Positions',
      `Are you sure you want to close ALL ${positions.length} active positions?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Close All Now',
          style: 'destructive',
          onPress: async () => {
            setSubmitting(true);
            try {
              const res = await closeAllPositions();
              if (res && (res.status === 'SUCCESS' || (res.closed_count ?? 0) > 0)) {
                Alert.alert('All Positions Closed', `Successfully closed ${res.closed_count ?? 0} positions.`);
                fetchAllData();
              } else {
                Alert.alert('Close All', res?.reason || 'No positions closed.');
              }
            } catch (err: any) {
              Alert.alert('Close Failed', err?.message || 'Network error closing positions.');
            } finally {
              setSubmitting(false);
            }
          },
        },
      ]
    );
  };"""

if old_handler in content:
    content = content.replace(old_handler, new_handler)

# 3. Update Buy and Sell onPress
old_buy_press = """              onPress={() => {
                setOrderType('BUY');
                handleExecuteOrder();
              }}"""

new_buy_press = """              onPress={() => handleExecuteOrder('BUY')}"""

old_sell_press = """              onPress={() => {
                setOrderType('SELL');
                handleExecuteOrder();
              }}"""

new_sell_press = """              onPress={() => handleExecuteOrder('SELL')}"""

content = content.replace(old_buy_press, new_buy_press)
content = content.replace(old_sell_press, new_sell_press)

# 4. Add Close All button in the Active Positions section header
old_pos_header = """        {/* Live Active Positions */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle} allowFontScaling={false}>
            ACTIVE POSITIONS ({positions.length})
          </Text>
        </View>"""

new_pos_header = """        {/* Live Active Positions */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle} allowFontScaling={false}>
            ACTIVE POSITIONS ({positions.length})
          </Text>
          {positions.length > 0 && (
            <TouchableOpacity
              style={styles.closeAllBtn}
              onPress={handleCloseAllPositions}
              disabled={submitting}
            >
              <Text style={styles.closeAllBtnText} allowFontScaling={false}>
                CLOSE ALL ({positions.length})
              </Text>
            </TouchableOpacity>
          )}
        </View>"""

content = content.replace(old_pos_header, new_pos_header)

# 5. Add Close button on each position card
old_ticket_top = """                  <Text
                    style={[styles.ticketProfit, { color: isProfit ? '#35E68A' : '#EF4444' }]}
                    allowFontScaling={false}
                  >
                    {isProfit ? '+' : ''}${(pos.profit || 0).toFixed(2)}
                  </Text>
                </View>"""

new_ticket_top = """                  <View style={styles.profitAndCloseCol}>
                    <Text
                      style={[styles.ticketProfit, { color: isProfit ? '#35E68A' : '#EF4444' }]}
                      allowFontScaling={false}
                    >
                      {isProfit ? '+' : ''}${(pos.profit || 0).toFixed(2)}
                    </Text>
                    <TouchableOpacity
                      style={styles.ticketCloseBtn}
                      onPress={() => handleClosePosition(pos.ticket, pos.symbol)}
                      disabled={submitting}
                    >
                      <Text style={styles.ticketCloseBtnText} allowFontScaling={false}>CLOSE</Text>
                    </TouchableOpacity>
                  </View>
                </View>"""

content = content.replace(old_ticket_top, new_ticket_top)

# 6. Append new styles for close buttons
extra_styles = """
  closeAllBtn: {
    backgroundColor: '#EF44441F',
    borderWidth: 1,
    borderColor: '#EF444460',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  closeAllBtnText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#EF4444',
    letterSpacing: 0.8,
  },
  profitAndCloseCol: {
    alignItems: 'flex-end',
    gap: 4,
  },
  ticketCloseBtn: {
    backgroundColor: '#EF444422',
    borderWidth: 1,
    borderColor: '#EF444455',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  ticketCloseBtnText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#EF4444',
    letterSpacing: 0.5,
  },
});
"""

if "closeAllBtn:" not in content:
    # replace the closing `});` at the very end
    idx = content.rfind("});")
    if idx != -1:
        content = content[:idx] + extra_styles

target.write_text(content, encoding="utf-8")
print("SUCCESS: TradesScreen.tsx updated with manual execution and close handlers!")
