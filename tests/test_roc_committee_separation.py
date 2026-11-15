"""Execute real committee and administrative scripts; the game engine is not emulated."""
import unittest
import test_roc_legislation as legislation
from test_roc_economic_council import ScriptState
from test_roc_allied_parties import read_script, one, ROOT, named_event


class CommitteeState(ScriptState):
    def __init__(self, effects, **variables):
        super().__init__(effects, **variables)
        self.random_calls = 0
        self.random_choice = 0
        self.focuses.add('gemingweiyuanhui')

ORIGINAL_BRANCHES = {'left': [([], ['zuoyilianmeng']),
          (['zuoyilianmeng'], ['lianluogemingyoudang']),
          (['lianluogemingyoudang', 'zuoyilianmeng'], ['tuijinsuoyouzhigeming']),
          (['lianluogemingyoudang', 'tuijinsuoyouzhigeming', 'zuoyilianmeng'],
           ['jiakuaigongsiheyingjincheng', 'tudigaigejijinhua']),
          (['jiakuaigongsiheyingjincheng', 'lianluogemingyoudang', 'tuijinsuoyouzhigeming', 'zuoyilianmeng'],
           ['qianghuagonghuigemingxing', 'tudigaigejijinhua']),
          (['jiakuaigongsiheyingjincheng',
            'lianluogemingyoudang',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'zuoyilianmeng'],
           ['qianghuagonghuigemingxing', 'weichinonghuiwuzhuang']),
          (['jiakuaigongsiheyingjincheng',
            'lianluogemingyoudang',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'zuoyilianmeng'],
           ['kuodanongcunhezuosheguimo', 'qianghuagonghuigemingxing']),
          (['jiakuaigongsiheyingjincheng',
            'kuodanongcunhezuosheguimo',
            'lianluogemingyoudang',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'zuoyilianmeng'],
           ['qianghuagonghuigemingxing']),
          (['jiakuaigongsiheyingjincheng',
            'kuodanongcunhezuosheguimo',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'zuoyilianmeng'],
           ['queligongyouzhijingjizhutidiwei']),
          (['jiakuaigongsiheyingjincheng',
            'kuodanongcunhezuosheguimo',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'queligongyouzhijingjizhutidiwei',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'zuoyilianmeng'],
           ['gemingjijinhua']),
          (['gemingjijinhua',
            'jiakuaigongsiheyingjincheng',
            'kuodanongcunhezuosheguimo',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'queligongyouzhijingjizhutidiwei',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'zuoyilianmeng'],
           ['youxiangongnongquanyi']),
          (['gemingjijinhua',
            'jiakuaigongsiheyingjincheng',
            'kuodanongcunhezuosheguimo',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'queligongyouzhijingjizhutidiwei',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'youxiangongnongquanyi',
            'zuoyilianmeng'],
           ['xianqililunlunzhan', 'zhengduogeminglingdaoquan']),
          (['gemingjijinhua',
            'jiakuaigongsiheyingjincheng',
            'kuodanongcunhezuosheguimo',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'queligongyouzhijingjizhutidiwei',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'xianqililunlunzhan',
            'youxiangongnongquanyi',
            'zuoyilianmeng'],
           ['zhengduogeminglingdaoquan']),
          (['gemingjijinhua',
            'jiakuaigongsiheyingjincheng',
            'kuodanongcunhezuosheguimo',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'queligongyouzhijingjizhutidiwei',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'xianqililunlunzhan',
            'youxiangongnongquanyi',
            'zhengduogeminglingdaoquan',
            'zuoyilianmeng'],
           ['dajixiuzhengfenzi']),
          (['dajixiuzhengfenzi',
            'gemingjijinhua',
            'jiakuaigongsiheyingjincheng',
            'kuodanongcunhezuosheguimo',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'queligongyouzhijingjizhutidiwei',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'xianqililunlunzhan',
            'youxiangongnongquanyi',
            'zhengduogeminglingdaoquan',
            'zuoyilianmeng'],
           ['jixugeming']),
          (['dajixiuzhengfenzi',
            'gemingjijinhua',
            'jiakuaigongsiheyingjincheng',
            'jixugeming',
            'kuodanongcunhezuosheguimo',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'queligongyouzhijingjizhutidiwei',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'xianqililunlunzhan',
            'youxiangongnongquanyi',
            'zhengduogeminglingdaoquan',
            'zuoyilianmeng'],
           []),
          (['gemingjijinhua',
            'jiakuaigongsiheyingjincheng',
            'kuodanongcunhezuosheguimo',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'queligongyouzhijingjizhutidiwei',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'youxiangongnongquanyi',
            'zhengduogeminglingdaoquan',
            'zuoyilianmeng'],
           ['xianqililunlunzhan']),
          (['jiakuaigongsiheyingjincheng',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'zuoyilianmeng'],
           ['kuodanongcunhezuosheguimo', 'queligongyouzhijingjizhutidiwei']),
          (['jiakuaigongsiheyingjincheng',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'queligongyouzhijingjizhutidiwei',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'zuoyilianmeng'],
           ['kuodanongcunhezuosheguimo']),
          (['jiakuaigongsiheyingjincheng',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'zuoyilianmeng'],
           ['queligongyouzhijingjizhutidiwei', 'weichinonghuiwuzhuang']),
          (['jiakuaigongsiheyingjincheng',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'queligongyouzhijingjizhutidiwei',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'zuoyilianmeng'],
           ['weichinonghuiwuzhuang']),
          (['jiakuaigongsiheyingjincheng',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'tuijinsuoyouzhigeming',
            'zuoyilianmeng'],
           ['queligongyouzhijingjizhutidiwei', 'tudigaigejijinhua']),
          (['jiakuaigongsiheyingjincheng',
            'lianluogemingyoudang',
            'qianghuagonghuigemingxing',
            'queligongyouzhijingjizhutidiwei',
            'tuijinsuoyouzhigeming',
            'zuoyilianmeng'],
           ['tudigaigejijinhua']),
          (['lianluogemingyoudang', 'tudigaigejijinhua', 'tuijinsuoyouzhigeming', 'zuoyilianmeng'],
           ['jiakuaigongsiheyingjincheng', 'weichinonghuiwuzhuang']),
          (['lianluogemingyoudang',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'zuoyilianmeng'],
           ['jiakuaigongsiheyingjincheng', 'kuodanongcunhezuosheguimo']),
          (['kuodanongcunhezuosheguimo',
            'lianluogemingyoudang',
            'tudigaigejijinhua',
            'tuijinsuoyouzhigeming',
            'weichinonghuiwuzhuang',
            'zuoyilianmeng'],
           ['jiakuaigongsiheyingjincheng'])],
 'center': [([], ['gemingtongyizhanxian']),
            (['gemingtongyizhanxian'], ['qianghuazhengzhituanjie']),
            (['gemingtongyizhanxian', 'qianghuazhengzhituanjie'], ['jijicanzhengyizheng']),
            (['gemingtongyizhanxian', 'jijicanzhengyizheng', 'qianghuazhengzhituanjie'],
             ['xiezhugongyegaizao', 'xiezhunongyegaizao']),
            (['gemingtongyizhanxian', 'jijicanzhengyizheng', 'qianghuazhengzhituanjie', 'xiezhugongyegaizao'],
             ['xiezhunongyegaizao']),
            (['gemingtongyizhanxian',
              'jijicanzhengyizheng',
              'qianghuazhengzhituanjie',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao'],
             ['luoshixinjingjifa']),
            (['gemingtongyizhanxian',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'qianghuazhengzhituanjie',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao'],
             ['zhichisansanzhizhengfu']),
            (['gemingtongyizhanxian',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'qianghuazhengzhituanjie',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'zhichisansanzhizhengfu'],
             ['jicengjibuhezuo', 'peihekaizhanqunzhongyundong']),
            (['gemingtongyizhanxian',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuazhengzhituanjie',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'zhichisansanzhizhengfu'],
             ['jicengjibuhezuo', 'qianghuahezuoxuanchuan']),
            (['gemingtongyizhanxian',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuahezuoxuanchuan',
              'qianghuazhengzhituanjie',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'zhichisansanzhizhengfu'],
             ['jicengjibuhezuo', 'yantaogeminglilun']),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuahezuoxuanchuan',
              'qianghuazhengzhituanjie',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'zhichisansanzhizhengfu'],
             ['tuijinkuadanghezuo', 'yantaogeminglilun']),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuahezuoxuanchuan',
              'qianghuazhengzhituanjie',
              'tuijinkuadanghezuo',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'zhichisansanzhizhengfu'],
             ['yantaogeminglilun', 'yazhifenliezhuyi']),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuahezuoxuanchuan',
              'qianghuazhengzhituanjie',
              'tuijinkuadanghezuo',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'yantaogeminglilun',
              'zhichisansanzhizhengfu'],
             ['yazhifenliezhuyi']),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuahezuoxuanchuan',
              'qianghuazhengzhituanjie',
              'tuijinkuadanghezuo',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'yantaogeminglilun',
              'yazhifenliezhuyi',
              'zhichisansanzhizhengfu'],
             ['yongbaogemingweiyuanhuizhengzhi']),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuahezuoxuanchuan',
              'qianghuazhengzhituanjie',
              'tuijinkuadanghezuo',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'yantaogeminglilun',
              'yazhifenliezhuyi',
              'yongbaogemingweiyuanhuizhengzhi',
              'zhichisansanzhizhengfu'],
             ['jingchenghezuo']),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'jingchenghezuo',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuahezuoxuanchuan',
              'qianghuazhengzhituanjie',
              'tuijinkuadanghezuo',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'yantaogeminglilun',
              'yazhifenliezhuyi',
              'yongbaogemingweiyuanhuizhengzhi',
              'zhichisansanzhizhengfu'],
             []),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuahezuoxuanchuan',
              'qianghuazhengzhituanjie',
              'tuijinkuadanghezuo',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'yazhifenliezhuyi',
              'zhichisansanzhizhengfu'],
             ['yantaogeminglilun']),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuahezuoxuanchuan',
              'qianghuazhengzhituanjie',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'yantaogeminglilun',
              'zhichisansanzhizhengfu'],
             ['tuijinkuadanghezuo']),
            (['gemingtongyizhanxian',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuahezuoxuanchuan',
              'qianghuazhengzhituanjie',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'yantaogeminglilun',
              'zhichisansanzhizhengfu'],
             ['jicengjibuhezuo']),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuazhengzhituanjie',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'zhichisansanzhizhengfu'],
             ['qianghuahezuoxuanchuan', 'tuijinkuadanghezuo']),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuazhengzhituanjie',
              'tuijinkuadanghezuo',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'zhichisansanzhizhengfu'],
             ['qianghuahezuoxuanchuan', 'yazhifenliezhuyi']),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'peihekaizhanqunzhongyundong',
              'qianghuazhengzhituanjie',
              'tuijinkuadanghezuo',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'yazhifenliezhuyi',
              'zhichisansanzhizhengfu'],
             ['qianghuahezuoxuanchuan']),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'qianghuazhengzhituanjie',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'zhichisansanzhizhengfu'],
             ['peihekaizhanqunzhongyundong', 'tuijinkuadanghezuo']),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'qianghuazhengzhituanjie',
              'tuijinkuadanghezuo',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'zhichisansanzhizhengfu'],
             ['peihekaizhanqunzhongyundong', 'yazhifenliezhuyi']),
            (['gemingtongyizhanxian',
              'jicengjibuhezuo',
              'jijicanzhengyizheng',
              'luoshixinjingjifa',
              'qianghuazhengzhituanjie',
              'tuijinkuadanghezuo',
              'xiezhugongyegaizao',
              'xiezhunongyegaizao',
              'yazhifenliezhuyi',
              'zhichisansanzhizhengfu'],
             ['peihekaizhanqunzhongyundong']),
            (['gemingtongyizhanxian', 'jijicanzhengyizheng', 'qianghuazhengzhituanjie', 'xiezhunongyegaizao'],
             ['xiezhugongyegaizao'])],
 'right': [([], ['youyilianmeng']),
           (['youyilianmeng'], ['ziyoudatongmeng']),
           (['youyilianmeng', 'ziyoudatongmeng'], ['jingjihuanjingfanglue']),
           (['jingjihuanjingfanglue', 'youyilianmeng', 'ziyoudatongmeng'],
            ['huanhexiangcundouzheng', 'yaoqiubaozhangminqiquanyi']),
           (['jingjihuanjingfanglue', 'yaoqiubaozhangminqiquanyi', 'youyilianmeng', 'ziyoudatongmeng'],
            ['huanhexiangcundouzheng', 'jianadaqiyejiaruhui']),
           (['huanhexiangcundouzheng',
             'jingjihuanjingfanglue',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['jianadaqiyejiaruhui', 'tuidongnongcunjingjihuazhuanxiang']),
           (['huanhexiangcundouzheng',
             'jingjihuanjingfanglue',
             'tuidongnongcunjingjihuazhuanxiang',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['jianadaqiyejiaruhui', 'tudiliuzhuanziyouhua']),
           (['huanhexiangcundouzheng',
             'jingjihuanjingfanglue',
             'tudiliuzhuanziyouhua',
             'tuidongnongcunjingjihuazhuanxiang',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['jianadaqiyejiaruhui']),
           (['huanhexiangcundouzheng',
             'jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'tudiliuzhuanziyouhua',
             'tuidongnongcunjingjihuazhuanxiang',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['tiyihuifuguangjiaosuo']),
           (['huanhexiangcundouzheng',
             'jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'tiyihuifuguangjiaosuo',
             'tudiliuzhuanziyouhua',
             'tuidongnongcunjingjihuazhuanxiang',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['gemingziyouhua']),
           (['gemingziyouhua',
             'huanhexiangcundouzheng',
             'jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'tiyihuifuguangjiaosuo',
             'tudiliuzhuanziyouhua',
             'tuidongnongcunjingjihuazhuanxiang',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['xuanyangzhengzhiminzhu']),
           (['gemingziyouhua',
             'huanhexiangcundouzheng',
             'jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'tiyihuifuguangjiaosuo',
             'tudiliuzhuanziyouhua',
             'tuidongnongcunjingjihuazhuanxiang',
             'xuanyangzhengzhiminzhu',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['fangkuanzudangshenhe', 'yaoqiusuxingxianzheng']),
           (['fangkuanzudangshenhe',
             'gemingziyouhua',
             'huanhexiangcundouzheng',
             'jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'tiyihuifuguangjiaosuo',
             'tudiliuzhuanziyouhua',
             'tuidongnongcunjingjihuazhuanxiang',
             'xuanyangzhengzhiminzhu',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['yaoqiusuxingxianzheng']),
           (['fangkuanzudangshenhe',
             'gemingziyouhua',
             'huanhexiangcundouzheng',
             'jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'tiyihuifuguangjiaosuo',
             'tudiliuzhuanziyouhua',
             'tuidongnongcunjingjihuazhuanxiang',
             'xuanyangzhengzhiminzhu',
             'yaoqiubaozhangminqiquanyi',
             'yaoqiusuxingxianzheng',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['zhiyidatonghui']),
           (['fangkuanzudangshenhe',
             'gemingziyouhua',
             'huanhexiangcundouzheng',
             'jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'tiyihuifuguangjiaosuo',
             'tudiliuzhuanziyouhua',
             'tuidongnongcunjingjihuazhuanxiang',
             'xuanyangzhengzhiminzhu',
             'yaoqiubaozhangminqiquanyi',
             'yaoqiusuxingxianzheng',
             'youyilianmeng',
             'zhiyidatonghui',
             'ziyoudatongmeng'],
            ['lunliuzuozhuang']),
           (['fangkuanzudangshenhe',
             'gemingziyouhua',
             'huanhexiangcundouzheng',
             'jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'lunliuzuozhuang',
             'tiyihuifuguangjiaosuo',
             'tudiliuzhuanziyouhua',
             'tuidongnongcunjingjihuazhuanxiang',
             'xuanyangzhengzhiminzhu',
             'yaoqiubaozhangminqiquanyi',
             'yaoqiusuxingxianzheng',
             'youyilianmeng',
             'zhiyidatonghui',
             'ziyoudatongmeng'],
            []),
           (['gemingziyouhua',
             'huanhexiangcundouzheng',
             'jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'tiyihuifuguangjiaosuo',
             'tudiliuzhuanziyouhua',
             'tuidongnongcunjingjihuazhuanxiang',
             'xuanyangzhengzhiminzhu',
             'yaoqiubaozhangminqiquanyi',
             'yaoqiusuxingxianzheng',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['fangkuanzudangshenhe']),
           (['huanhexiangcundouzheng',
             'jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'tuidongnongcunjingjihuazhuanxiang',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['tiyihuifuguangjiaosuo', 'tudiliuzhuanziyouhua']),
           (['huanhexiangcundouzheng',
             'jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'tiyihuifuguangjiaosuo',
             'tuidongnongcunjingjihuazhuanxiang',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['tudiliuzhuanziyouhua']),
           (['huanhexiangcundouzheng',
             'jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['tiyihuifuguangjiaosuo', 'tuidongnongcunjingjihuazhuanxiang']),
           (['huanhexiangcundouzheng',
             'jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'tiyihuifuguangjiaosuo',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['tuidongnongcunjingjihuazhuanxiang']),
           (['jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['huanhexiangcundouzheng', 'tiyihuifuguangjiaosuo']),
           (['jianadaqiyejiaruhui',
             'jingjihuanjingfanglue',
             'tiyihuifuguangjiaosuo',
             'yaoqiubaozhangminqiquanyi',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['huanhexiangcundouzheng']),
           (['huanhexiangcundouzheng', 'jingjihuanjingfanglue', 'youyilianmeng', 'ziyoudatongmeng'],
            ['tuidongnongcunjingjihuazhuanxiang', 'yaoqiubaozhangminqiquanyi']),
           (['huanhexiangcundouzheng',
             'jingjihuanjingfanglue',
             'tuidongnongcunjingjihuazhuanxiang',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['tudiliuzhuanziyouhua', 'yaoqiubaozhangminqiquanyi']),
           (['huanhexiangcundouzheng',
             'jingjihuanjingfanglue',
             'tudiliuzhuanziyouhua',
             'tuidongnongcunjingjihuazhuanxiang',
             'youyilianmeng',
             'ziyoudatongmeng'],
            ['yaoqiubaozhangminqiquanyi'])]}


class CommitteeSeparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.effects = {}
        for directory in ('scripted_effects', 'scripted_triggers'):
            for path in (ROOT / 'common' / directory).glob('ROC*.txt'):
                cls.effects.update(dict(read_script(str(path))))

    def run_effect(self, s, name):
        self.assertTrue(name in self.effects, 'missing behavior: ' + name)
        s.run(self.effects[name])

    def test_original_random_branch_graph_has_same_78_states_and_terminal_endings(self):
        for side, states in ORIGINAL_BRANCHES.items():
            self.assertEqual(len(states), 26)
            selected = []
            selector = self.effects['ROC_committee_select_' + side]
            from test_roc_economic_council_runtime_syntax import walk
            complete = self.effects['ROC_committee_complete_' + side]
            mapping = {int(one(one(value, 'limit'), 'check_variable')[1][1]): next(v for k,v in value if k == 'complete_national_focus')
                       for k,value in walk(complete) if k == 'if' and any(x == 'complete_national_focus' for x,_ in value)}
            for done, expected in states:
                actual = set()
                for branch in (0, 1):
                    s = CommitteeState(self.effects)
                    s.focuses.update(done)
                    s.random_choice = branch
                    s.run(selector)
                    index = s.vars.get('ROC_committee_' + side + '_agenda', 0)
                    if index:
                        actual.add(mapping[int(index)])
                        prior_calls = s.random_calls
                        s.run(selector)
                        self.assertEqual(s.random_calls, prior_calls)
                        self.assertEqual(s.vars['ROC_committee_' + side + '_agenda'], index)
                self.assertEqual(actual, set(expected), (side, done))

    def test_agenda_is_selected_before_timer_and_does_not_refresh(self):
        s = CommitteeState(self.effects)
        self.run_effect(s, 'ROC_committee_daily')
        self.assertEqual(s.vars['ROC_committee_left_agenda'], 1)
        s.missions['ROC_decision_zuopai'] = 83
        for _ in range(5): self.run_effect(s, 'ROC_committee_daily')
        self.assertEqual(s.vars['ROC_committee_left_agenda'], 1)
        self.assertEqual(s.missions['ROC_decision_zuopai'], 83)
        self.run_effect(s, 'ROC_committee_complete_left')
        self.assertIn('zuoyilianmeng', s.focuses)
        self.assertEqual(s.vars['ROC_committee_left_progress'], 1)

    def test_leader_uses_actual_focus_count_and_load_is_idempotent(self):
        s = CommitteeState(self.effects)
        s.focuses.update({'zuoyilianmeng', 'lianluogemingyoudang', 'tuijinsuoyouzhigeming'})
        s.vars['ROC_committee_radicalization'] = 50
        self.run_effect(s, 'ROC_committee_daily')
        self.assertEqual(s.vars['ROC_committee_leading_side'], 1)
        self.assertEqual(s.vars['ROC_committee_left_progress'], 3)
        for _ in range(3): self.run_effect(s, 'ROC_committee_daily')
        self.assertEqual(s.vars['ROC_committee_radicalization'], 50)
        s.focuses.update({'gemingtongyizhanxian', 'qianghuazhengzhituanjie'})
        self.run_effect(s, 'ROC_committee_refresh_progress')
        self.assertEqual(s.vars['ROC_committee_leading_side'], 0)

    def test_manually_completed_agenda_advances_without_resetting_countdown_or_bonus(self):
        s = CommitteeState(self.effects)
        self.run_effect(s, 'ROC_committee_daily')
        s.missions['ROC_decision_zuopai'] = 83
        s.focuses.add('zuoyilianmeng')
        self.run_effect(s, 'ROC_committee_daily')
        self.assertEqual(s.vars['ROC_committee_left_agenda'], 2)
        self.assertEqual(s.missions['ROC_decision_zuopai'], 83)
        self.assertEqual(s.vars['ROC_committee_left_progress'], 1)
        self.assertEqual(s.vars['ROC_committee_radicalization'], 0)

    def test_postwar_preserves_actual_final_progress_after_focus_tree_switch(self):
        s = CommitteeState(self.effects)
        s.cosmetic_tag = 'ROC_tongyi'
        s.focuses.update({'zuoyilianmeng','tuijinsuoyouzhigeming','tudigaigejijinhua'})
        self.run_effect(s, 'ROC_enter_postwar_tree')
        self.assertEqual(s.vars['ROC_committee_left_progress'], 3)
        for _ in range(3): self.run_effect(s, 'ROC_committee_daily')
        self.assertEqual(s.vars['ROC_committee_left_progress'], 3)
        self.assertEqual(s.vars['ROC_committee_left_agenda'], 0)

    def test_objection_is_single_use_and_old_popup_cannot_delay_new_agenda(self):
        s = CommitteeState(self.effects)
        self.run_effect(s, 'ROC_committee_daily')
        s.missions['ROC_decision_zuopai'] = 60
        s.vars.update(ROC_committee_leading_side=1, ROC_committee_radicalization=75)
        self.run_effect(s, 'ROC_committee_open_objection')
        self.assertEqual(s.vars['ROC_committee_objection_target'], 1)
        self.run_effect(s, 'ROC_committee_delay_21')
        self.assertEqual(s.missions['ROC_decision_zuopai'], 81)
        self.run_effect(s, 'ROC_committee_delay_21')
        self.assertEqual(s.missions['ROC_decision_zuopai'], 81)
        s.flags.discard('ROC_committee_objection_cooldown')
        self.run_effect(s, 'ROC_committee_open_objection')
        self.run_effect(s, 'ROC_committee_complete_left')
        self.run_effect(s, 'ROC_committee_daily')
        before = s.missions['ROC_decision_zuopai']
        self.run_effect(s, 'ROC_committee_delay_21')
        self.assertEqual(s.missions['ROC_decision_zuopai'], before)

    def test_terminal_and_postwar_states_never_activate_or_delay(self):
        for ending in ('jixugeming', 'jingchenghezuo', 'lunliuzuozhuang', 'postwar'):
            s = CommitteeState(self.effects)
            self.run_effect(s, 'ROC_committee_daily')
            s.vars['ROC_committee_leading_side'] = 1
            self.run_effect(s, 'ROC_committee_open_objection')
            if ending == 'postwar': s.flags.add('ROC_postwar_active')
            else: s.focuses.add(ending)
            before = dict(s.missions)
            self.run_effect(s, 'ROC_committee_delay_21')
            self.assertEqual(s.missions, before)
            self.run_effect(s, 'ROC_committee_daily')
            self.assertEqual(s.vars['ROC_committee_left_agenda'], 0)
            self.assertNotIn('ROC_committee_objection_pending', s.flags)

    def test_leaving_committee_cancels_old_native_missions(self):
        s = CommitteeState(self.effects)
        self.run_effect(s, 'ROC_committee_daily')
        s.focuses.clear()
        self.run_effect(s, 'ROC_committee_daily')
        self.assertNotIn('ROC_decision_zuopai', s.missions)
        self.assertNotIn('ROC_decision_zhongpai', s.missions)
        self.assertNotIn('ROC_decision_youpai', s.missions)

    def test_weekly_probability_thresholds_bounds_and_cooldown(self):
        from test_roc_economic_council_runtime_syntax import walk
        weights = [tuple(k for k,_ in v) for k,v in walk(self.effects['ROC_committee_weekly']) if k == 'random_list']
        self.assertEqual(weights, [('35','65'),('20','80'),('10','90')])
        for initial, opens in ((22,False),(23,True),(48,True),(73,True),(100,True)):
            for branch in (0,1):
                s = CommitteeState(self.effects)
                s.focuses.update({'zuoyilianmeng','lianluogemingyoudang','tuijinsuoyouzhigeming'})
                self.run_effect(s,'ROC_committee_daily')
                s.vars['ROC_committee_radicalization'] = initial
                s.random_choice = branch
                self.run_effect(s,'ROC_committee_weekly')
                self.assertEqual(s.vars['ROC_committee_radicalization'], min(initial+2,100))
                self.assertEqual('ROC_committee_objection_pending' in s.flags, opens and branch == 0)
                if opens and branch == 0:
                    self.assertEqual(s.flag_days['ROC_committee_objection_cooldown'],45)
                    self.assertEqual(s.flag_days['ROC_committee_objection_pending'],8)
                    self.run_effect(s,'ROC_committee_delay_21')
                    before=len(s.events)
                    self.run_effect(s,'ROC_committee_open_objection')
                    self.assertEqual(len(s.events),before)
        s = CommitteeState(self.effects)
        self.run_effect(s,'ROC_committee_daily')
        self.run_effect(s,'ROC_committee_weekly')
        self.assertEqual(s.vars['ROC_committee_radicalization'],0)

    def test_paid_response_boundary_and_target_stay_locked_when_leader_changes(self):
        for favor in (14,15):
            s = CommitteeState(self.effects)
            self.run_effect(s,'ROC_committee_daily')
            s.missions.update(ROC_decision_zuopai=60,ROC_decision_youpai=40)
            s.vars.update(ROC_committee_leading_side=1,ROC_committee_radicalization=6)
            self.run_effect(s,'ROC_committee_open_objection')
            s.vars['ROC_committee_leading_side']=3
            s.pp=0;s.vars['ROC_ma_left_favor']=favor
            self.run_effect(s,'ROC_committee_delay_7')
            self.assertEqual(s.missions['ROC_decision_zuopai'],67 if favor==15 else 60)
            self.assertEqual(s.missions['ROC_decision_youpai'],40)
            self.assertEqual(s.pp,0)
            self.assertEqual(s.vars['ROC_ma_left_favor'],0 if favor==15 else 14)
            if favor==15:
                self.assertEqual(s.vars['ROC_committee_radicalization'],0)
                self.run_effect(s,'ROC_committee_delay_7')
                self.assertEqual(s.pp,0)
                self.assertEqual(s.missions['ROC_decision_zuopai'],67)

    def test_new_leading_completion_adds_reaction_once(self):
        s=CommitteeState(self.effects)
        s.focuses.update({'zuoyilianmeng','lianluogemingyoudang','tuijinsuoyouzhigeming'})
        self.run_effect(s,'ROC_committee_daily')
        self.run_effect(s,'ROC_committee_complete_left')
        self.assertEqual(s.vars['ROC_committee_left_progress'],4)
        self.assertEqual(s.vars['ROC_committee_radicalization'],6)
        self.run_effect(s,'ROC_committee_complete_left')
        self.run_effect(s,'ROC_committee_daily')
        self.assertEqual(s.vars['ROC_committee_radicalization'],6)

    def test_objection_events_have_guarded_timeouts_and_stale_close(self):
        events=read_script('events/ROC_committee.txt')
        for ident in range(1,4):
            event=named_event(events,'ROC_committee.'+str(ident))
            self.assertEqual(one(event,'timeout_days'),'7')
            s=CommitteeState(self.effects)
            self.run_effect(s,'ROC_committee_daily')
            s.vars['ROC_committee_leading_side']=1
            self.run_effect(s,'ROC_committee_open_objection')
            s.flags.discard('ROC_committee_objection_pending')
            before=(s.pp,dict(s.vars),dict(s.missions))
            for key,option in event:
                if key!='option':continue
                if one(option,'name')=='ROC_committee_stale_close':
                    self.assertTrue(s.passes(one(option,'trigger')))
                    self.assertFalse(any(k=='hidden_effect' for k,_ in option))
                for k,value in option:
                    if k=='hidden_effect':s.run(value)
            self.assertEqual((s.pp,s.vars,s.missions),before)


class AdministrationSeparation(unittest.TestCase):
    setUpClass = classmethod(legislation.Legislation.setUpClass.__func__)
    state = legislation.Legislation.state
    run_effect = legislation.Legislation.run_effect
    submit = legislation.Legislation.submit
    def test_no_committee_still_requires_independent_approval(self):
        s = self.state()
        s.focuses.discard('gemingweiyuanhui')
        self.assertFalse(s.passes(one(self.projects['ROC_econ_yu_pilot'], 'available')))
        self.submit(s)
        self.run_effect(s, 'ROC_bill_prepare_materials')
        self.run_effect(s, 'ROC_bill_vote')
        self.assertEqual(s.vars['ROC_bill_stage'], 3)

    def test_party_progress_records_and_pressure_cannot_change_readiness(self):
        s = self.state()
        self.submit(s)
        self.run_effect(s, 'ROC_bill_prepare_signatures')
        expected = (s.vars['ROC_bill_support'], s.vars['ROC_bill_requirement'])
        s.flags.update({'ROC_bill_rural_record', 'ROC_bill_credit_record'})
        s.focuses.update({'jingchenghezuo', 'jixugeming', 'qianghuazhengzhituanjie'})
        s.vars.update(ROC_VAR_youyi_base=1, ROC_VAR_zuoyi_base=1, ROC_committee_radicalization=100)
        self.run_effect(s, 'ROC_bill_refresh_support')
        self.assertEqual((s.vars['ROC_bill_support'], s.vars['ROC_bill_requirement']), expected)

    def test_stage_two_legacy_migrates_both_old_support_layer_versions(self):
        for layered in (False,True):
            s=self.state()
            s.vars.update(ROC_bill_id=1,ROC_bill_stage=2,ROC_bill_days_left=20,ROC_bill_tactic=0)
            if layered:s.flags.add('ROC_bill_support_layers_ready')
            self.run_effect(s,'ROC_bill_daily')
            self.assertEqual(s.pp,200)
            self.assertEqual(s.vars['ROC_bill_days_left'],19)
            self.assertEqual(s.vars['ROC_bill_support'],2)
            self.assertEqual(s.vars['ROC_bill_economic_support'],2)
            self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'],1000)
            self.run_effect(s,'ROC_bill_vote')
            self.assertEqual(s.vars['ROC_bill_stage'],3)

    def test_high_conflict_industries_need_guarantees_without_policy_basis(self):
        for person in (0,3,4):
            for preparation in ('materials','signatures'):
                s=self.state(person)
                s.focuses.discard(legislation.PEOPLE[person][2])
                self.submit(s)
                self.run_effect(s,'ROC_bill_prepare_'+preparation)
                if preparation=='materials':
                    self.assertEqual(s.vars['ROC_bill_stage'],0,(person,preparation))
                    self.assertIn('ROC_bill_sector_tabled',s.flags)
                else:
                    self.assertEqual(s.vars['ROC_bill_stage'],2,(person,preparation))
                    self.assertEqual(s.vars['ROC_bill_economic_support'],2)
                    self.run_effect(s,'ROC_bill_conditional')
                    self.assertEqual(s.vars['ROC_bill_stage'],3)
                    self.assertEqual(s.vars['ROC_bill_outcome'],2)

    def test_low_conflict_pilots_keep_cost_audit_and_late_policy_routes(self):
        for person in (1,2):
            s=self.state(person)
            s.focuses.discard(legislation.PEOPLE[person][2])
            self.submit(s)
            self.assertEqual(s.vars.get('ROC_bill_sector_requirement'),1)
            self.run_effect(s,'ROC_bill_prepare_materials')
            self.assertEqual(s.vars['ROC_bill_stage'],2)
            self.run_effect(s,'ROC_bill_vote')
            self.assertEqual(s.vars['ROC_bill_stage'],3)
            s=self.state(person)
            s.missions['ROC_decision_bop_jingjidahui']=700
            self.run_effect(s,'ROC_econ_refresh')
            self.submit(s)
            self.run_effect(s,'ROC_bill_prepare_party')
            self.assertEqual(s.vars['ROC_bill_stage'],2)
            self.run_effect(s,'ROC_bill_vote')
            self.assertEqual(s.vars['ROC_bill_stage'],3)

    def test_sector_requirements_for_all_projects_and_approved_save_bypass(self):
        for person in range(5):
            for expansion in (False,True):
                s=self.state(person,expansion)
                self.submit(s)
                self.assertEqual(s.vars.get('ROC_bill_sector_requirement'),
                                 2 if expansion or person in (0,3,4) else 1)
                self.run_effect(s,'ROC_bill_prepare_materials')
                self.assertEqual(s.vars['ROC_bill_stage'],2)
                self.run_effect(s,'ROC_bill_vote')
                self.assertEqual(s.vars['ROC_bill_stage'],3)
        s=self.state()
        s.focuses.discard(legislation.PEOPLE[0][2])
        s.vars.update(ROC_bill_stage=3,ROC_bill_id=1,ROC_bill_economic_support=1)
        self.run_effect(s,'ROC_bill_daily')
        self.assertEqual(s.vars['ROC_bill_stage'],3)
        self.assertEqual(s.vars['ROC_bill_economic_support'],1)

    def test_pilot_matrix_has_real_guarantee_advantages(self):
        advantages=[]
        for person in range(5):
            for policy in (False,True):
                for days in (1000,700):
                    for audit in (False,True):
                        approved={}
                        for preparation in ('materials','signatures'):
                            s=self.state(person)
                            if not policy:s.focuses.discard(legislation.PEOPLE[person][2])
                            s.missions['ROC_decision_bop_jingjidahui']=days
                            if audit:s.flags.add('ROC_bill_supervision')
                            self.run_effect(s,'ROC_econ_refresh')
                            self.submit(s)
                            self.run_effect(s,'ROC_bill_prepare_'+preparation)
                            if s.vars['ROC_bill_stage']==2:
                                if s.passes([('ROC_bill_enough_support','yes')]):
                                    self.run_effect(s,'ROC_bill_vote')
                                else:
                                    self.run_effect(s,'ROC_bill_conditional')
                            approved[preparation]=s.vars['ROC_bill_stage']==3
                        if approved['signatures'] and not approved['materials']:
                            advantages.append((person,policy,days,audit))
        self.assertEqual(len(advantages),9)
        self.assertEqual({person for person,_,_,_ in advantages},{0,3,4})
        self.assertTrue(all(not policy for _,policy,_,_ in advantages))

    def test_economic_hover_uses_current_state_without_idle_fake_counts(self):
        from test_sichuan_red_opportunity import parse_localization
        rules,_=parse_localization((ROOT/'localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml').read_bytes())
        text=rules['ROC_bill_submit_desc']
        for name in ('ROC_bill_name','ROC_bill_stage_text','ROC_bill_readiness_text','ROC_bill_days_text','ROC_bill_outcome_text'):
            self.assertIn('[ROOT.'+name+']',text)
        self.assertNotIn('[?ROC_bill_support',text)
        for name in ('materials','signatures','party'):
            self.assertIn('[?ROC_bill_sector_requirement|0]',rules['ROC_bill_'+name+'_tt'])


if __name__ == '__main__': unittest.main()
