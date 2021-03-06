# -*- encoding=utf8 -*-
from poco.proxy import UIObjectProxy
from poco.exceptions import PocoNoSuchNodeException
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from CommonPackage.GlobalParameter import waitTime
from DbHelper.DbHelper import DbHelper
from Product.GetsData import get_shopName, crawl_status_code
from Send_Message import send_text
from StoreInfo.StoreSellScore import GetStoreName
from Operate.SwitchingPosition import SwithPosition
from Operate.SearchDrug import SearchDrugPage
from Product import ProductInfo
import time
from Operate.BackHomePage import BackHomePage
from .SearchPartProduct import get_goods


def SearchCatchStore(storeName: str, poco, device, DeviceNum: str, DeviceType: int):
    # 查找到该门店的相关信息
    AllClassifyInputClickNum = 0  # 大类进入点击小类的次数
    IsAllClassifyInput = False  # 是否从大类搜索进入(默认不是)
    DbContext = DbHelper()

    # result = DbContext.GetStorePoint(storeId)
    result = DbContext.GetStorePointForName(storeName)
    if len(result) == 1:
        # address字段可能找不到这个店，用AnchorPoint才能找到这个店
        strs = str(result[0]['AnchorPoint']).split(';')
        StoreAddress = strs[0]
        StoreName = result[0]['shopName']
        StoreCity = result[0]['City']
        storeId = result[0]['mtWmPoiId']

        IsAddress = SwithPosition(poco, StoreAddress, StoreCity, storeName, 0)  # 切换定位
        isExists = getStore(IsAddress, poco, DeviceNum,
                            IsAllClassifyInput, StoreName, device)
        if(not isExists):
            BackHomePage(poco, DbContext, DeviceNum, device)  # 返回首页
            StoreAddress = result[0]['address']
            IsAddress = SwithPosition(poco, StoreAddress, StoreCity, storeName, 0)  # 切换定位
            isExists = getStore(IsAddress, poco, DeviceNum, IsAllClassifyInput, StoreName, device)
            if(not isExists):
                # DbContext.AddLog(DeviceNum, 2, '爬取['+StoreName+']失败，没找到店铺')
                print('该店铺不存在！')
    pass


def search_store(storeName, poco, device, addr, city, shopid):
    IsAllClassifyInput = False  # 是否从大类搜索进入(默认不是)
    IsAddress = SwithPosition(poco, addr, city, storeName, 0)  # 切换定位
    getStore(IsAddress, poco, IsAllClassifyInput, storeName, device, shopid)


def DealStoreName(shopName: str):
    symbolList = ['(', ')', '（', '）', ' ']
    for item in symbolList:
        shopName = shopName.replace(item, '')
    return shopName


def getStore(IsAddress, poco, IsAllClassifyInput, StoreName, device, shopid):
    if not IsAddress:
        return False
    try:
        poco.swipe([0.5, 0.6], [0.5, 0.4], duration=0.3)
        time.sleep(3)
        if poco(text="买药").exists():
            poco(text="买药").wait(waitTime).click([0, 0])
        if poco(text='医药新人礼包').exists():
            poco("android.widget.FrameLayout").offspring("android:id/content").child(
                "android.widget.FrameLayout").child(
                "android.widget.FrameLayout").child("android.widget.FrameLayout").child(
                "android.widget.FrameLayout").child(
                "android.widget.FrameLayout").child("android.widget.FrameLayout")[2].child(
                "android.widget.ImageView").click()

    except PocoNoSuchNodeException:
        print('\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~o(╥﹏╥)o 第一个定位点无买药 o(╥﹏╥)o~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        IsAddress = False
        pass
# -------------------------------------------------------
    if poco(text='会员卡包').exists():
        poco('com.sankuai.meituan.takeoutnew:id/tv_medicine_more_entrance').click()
    poco('com.sankuai.meituan.takeoutnew:id/tv_header_search_view').wait(10).click()
    time.sleep(3)  # 睡眠一段时间等待页面加载
    poco("com.sankuai.meituan.takeoutnew:id/txt_search_keyword").click()
    poco("com.sankuai.meituan.takeoutnew:id/txt_search_keyword").set_text(StoreName)
    time.sleep(1)  # 睡眠一段时间等待页面加载
    poco("com.sankuai.meituan.takeoutnew:id/search_tv").click()
    time.sleep(3)  # 睡眠一段时间等待页面加载
# ----------------------------------------------------------
    storeNames = poco("com.sankuai.meituan.takeoutnew:id/list_poiSearch_poiList").child("android.widget.LinearLayout").wait(5)
    a = 0
    time.sleep(5)
    for sName in storeNames:
        if sName.offspring("com.sankuai.meituan.takeoutnew:id/textview_poi_name").exists():
            stName = DealStoreName(sName.offspring("com.sankuai.meituan.takeoutnew:id/textview_poi_name").get_text())
            print("店名：" + stName)
            a = handle_storeName(StoreName, stName, a, poco, sName, device, shopid)

    if poco("com.sankuai.meituan.takeoutnew:id/list_poiSearch_poiList").child("android.widget.RelativeLayout").exists():
        storeNames = poco("com.sankuai.meituan.takeoutnew:id/list_poiSearch_poiList").child("android.widget.RelativeLayout").wait(5)
        for sName in storeNames:
            if sName.offspring("com.sankuai.meituan.takeoutnew:id/poi_cate_poi_name").exists():
                stName = DealStoreName(sName.offspring("com.sankuai.meituan.takeoutnew:id/poi_cate_poi_name").get_text())
                print("店名：" + stName)
                a = handle_storeName(StoreName, stName, a, poco, sName, device, shopid)

    if a == 0:
        content = '监控到：' + StoreName + '--根据地址没有找到店名！'
        send_text(content)
        print(content)
    pass


def handle_storeName(StoreName, stName, a, poco, sName, device, shopid):
    if stName in DealStoreName(StoreName):
        a += 1
        if poco('com.sankuai.meituan.takeoutnew:id/imageview_mt_delivery').exists():  # 出现全城送
            sName.wait(waitTime).click()
            if poco(text='本店休息啦').exists():
                poco.swipe([0.5, 0.9], [0.5, 0.8], duration=0.3)
            time.sleep(5)
        else:
            sName.wait(waitTime).click()
            time.sleep(1)
            if poco(text='本店休息啦').exists():
                poco.swipe([0.5, 0.9], [0.5, 0.8], duration=0.3)
        poco('com.sankuai.meituan.takeoutnew:id/search_background').click()  # 点击搜索框
        get_goods(poco, device, stName, shopid)
        time.sleep(1)
        try:
            poco('com.sankuai.meituan.takeoutnew:id/img_back_gray').click()  # 从药品列表页再返回
        except:
            poco('com.sankuai.meituan.takeoutnew:id/img_back_light').click()
    else:
        pass
    return a


# 是否点击夜间送药
def ClickClassify(poco, AllClassifyInputClickNum):
    if AllClassifyInputClickNum == 1:
        if poco(text="夜间送药").exists():
            poco(text="夜间送药").wait(waitTime).click()
            return True
        else:
            return False
    else:
        return False
