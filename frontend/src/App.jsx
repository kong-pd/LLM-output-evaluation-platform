import{BrowserRouter,Routes,Route,Link}from"react-router-dom";
import UploadPage from"./pages/UploadPage";
import DashboardPage from"./pages/DashboardPage";
import DatasetPage from"./pages/DatasetPage";
export default function App(){return(<BrowserRouter><nav><Link to="/">Dashboard</Link><Link to="/upload">Upload</Link></nav><Routes><Route path="/" element={<DashboardPage/>}/><Route path="/upload" element={<UploadPage/>}/><Route path="/datasets/:id" element={<DatasetPage/>}/></Routes></BrowserRouter>)}
